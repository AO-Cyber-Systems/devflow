import Foundation

/// Manages the connection to the Python bridge backend.
@Observable
@MainActor
class ConnectionState {
    // MARK: - State

    var isConnected = false
    var connectionError: String?
    var lastPingTime: Date?
    var isHealthy = true

    // MARK: - Dependencies

    @ObservationIgnored let bridge: PythonBridge
    @ObservationIgnored private var healthCheckTask: Task<Void, Never>?

    // MARK: - Configuration

    private let healthCheckInterval: Duration = .seconds(30)
    private let maxReconnectAttempts = 5

    // MARK: - Initialization

    init(bridge: PythonBridge) {
        self.bridge = bridge
    }

    deinit {
        healthCheckTask?.cancel()
    }

    // MARK: - Actions

    func connect() async {
        do {
            try await bridge.start()
            isConnected = await bridge.isConnected
            connectionError = nil
            startHealthCheck()
        } catch {
            isConnected = false
            connectionError = error.localizedDescription
        }
    }

    func disconnect() async {
        stopHealthCheck()
        await bridge.stop()
        isConnected = false
    }

    func reconnect() async {
        await disconnect()
        await connect()
    }

    // MARK: - Health Check

    /// Start periodic health checks.
    func startHealthCheck() {
        guard healthCheckTask == nil else { return }

        healthCheckTask = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: self?.healthCheckInterval ?? .seconds(30))

                guard !Task.isCancelled else { break }
                guard let self = self else { break }

                await self.ping()
            }
        }
    }

    /// Stop periodic health checks.
    func stopHealthCheck() {
        healthCheckTask?.cancel()
        healthCheckTask = nil
    }

    /// Ping the backend to check connection health.
    func ping() async {
        do {
            struct PingResponse: Codable {
                let pong: Bool
                let timestamp: Double?
            }
            let response: PingResponse = try await bridge.call("system.ping")
            if response.pong {
                lastPingTime = Date()
                isHealthy = true
                if !isConnected {
                    isConnected = true
                    connectionError = nil
                }
            }
        } catch {
            isHealthy = false
            await handleConnectionLost()
        }
    }

    /// Handle lost connection with automatic reconnection.
    private func handleConnectionLost() async {
        isConnected = false

        // Exponential backoff retry
        var delay: UInt64 = 1_000_000_000 // 1 second
        let maxDelay: UInt64 = 30_000_000_000 // 30 seconds

        for attempt in 1...maxReconnectAttempts {
            try? await Task.sleep(nanoseconds: delay)

            do {
                try await bridge.start()
                isConnected = await bridge.isConnected
                if isConnected {
                    connectionError = nil
                    isHealthy = true
                    return
                }
            } catch {
                connectionError = "Reconnection attempt \(attempt) failed"
                delay = min(delay * 2, maxDelay)
            }
        }

        // Give up after max attempts
        connectionError = "Failed to reconnect after \(maxReconnectAttempts) attempts"
        isHealthy = false
    }
}
