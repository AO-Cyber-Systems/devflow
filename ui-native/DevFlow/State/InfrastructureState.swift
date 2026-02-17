import Foundation

/// Manages infrastructure status, domains, and certificates.
@Observable
@MainActor
class InfrastructureState {
    // MARK: - State

    var infraStatus: InfraStatus = .unknown
    var isLoadingInfra = false
    var isPolling = false

    // Domains
    var domainStatuses: [DomainStatus] = []
    var certificateInfo: CertificateInfo = .empty
    var hostsEntries: [String] = []
    var isLoadingDomains = false
    var isRegeneratingCerts = false
    var showAddDomain = false

    // MARK: - Dependencies

    @ObservationIgnored private let bridge: PythonBridge
    @ObservationIgnored private let notifications: NotificationState
    @ObservationIgnored private var pollingTask: Task<Void, Never>?

    // MARK: - Configuration

    private let pollingInterval: Duration = .seconds(10)

    // MARK: - Computed Properties

    var domainsNeedingHostsEntry: Int {
        domainStatuses.filter { !$0.isWildcard && !$0.inHostsFile }.count
    }

    // MARK: - Initialization

    init(bridge: PythonBridge, notifications: NotificationState) {
        self.bridge = bridge
        self.notifications = notifications
    }

    deinit {
        pollingTask?.cancel()
    }

    // MARK: - Polling

    /// Start automatic status polling when infrastructure is running.
    func startPolling() {
        guard pollingTask == nil else { return }
        isPolling = true

        pollingTask = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: self?.pollingInterval ?? .seconds(10))

                guard !Task.isCancelled else { break }
                guard let self = self else { break }

                // Only poll if not currently loading
                if !self.isLoadingInfra {
                    await self.refreshSilently()
                }
            }
        }
    }

    /// Stop automatic status polling.
    func stopPolling() {
        pollingTask?.cancel()
        pollingTask = nil
        isPolling = false
    }

    /// Refresh without showing loading indicator (for polling).
    private func refreshSilently() async {
        do {
            infraStatus = try await bridge.call("infra.status")
        } catch {
            // Silently ignore errors during polling
        }
    }

    // MARK: - Infrastructure Actions

    func refresh() async {
        isLoadingInfra = true
        defer { isLoadingInfra = false }

        do {
            infraStatus = try await bridge.call("infra.status")
        } catch {
            notifications.add(.error("Failed to get infrastructure status: \(error.localizedDescription)"))
        }
    }

    func start() async {
        isLoadingInfra = true
        defer { isLoadingInfra = false }

        do {
            let _: Bool = try await bridge.call("infra.start")
            notifications.add(.success("Infrastructure started"))
            await refresh()
            startPolling()  // Auto-start polling when infra starts
        } catch {
            notifications.add(.error("Failed to start infrastructure: \(error.localizedDescription)"))
        }
    }

    func stop() async {
        isLoadingInfra = true
        defer { isLoadingInfra = false }

        do {
            let _: Bool = try await bridge.call("infra.stop")
            notifications.add(.success("Infrastructure stopped"))
            stopPolling()  // Stop polling when infra stops
            await refresh()
        } catch {
            notifications.add(.error("Failed to stop infrastructure: \(error.localizedDescription)"))
        }
    }

    // MARK: - Domain Actions

    func loadDomains() async {
        isLoadingDomains = true
        defer { isLoadingDomains = false }

        do {
            let response: DomainsListResponse = try await bridge.call("domains.list")
            domainStatuses = response.domains
            certificateInfo = response.certInfo
            hostsEntries = response.hostsEntries
        } catch {
            notifications.add(.error("Failed to load domains: \(error.localizedDescription)"))
        }
    }

    func addDomain(_ domain: String, source: String = "user") async {
        do {
            let response: DomainAddResponse = try await bridge.call(
                "domains.add",
                params: ["domain": domain, "source": source]
            )
            if response.success {
                notifications.add(.success(response.message ?? "Domain added"))
                await loadDomains()

                // Auto-regenerate if needed
                if response.needsCertRegen == true {
                    await regenerateCertificates()
                }
            } else if let error = response.error {
                notifications.add(.error("Failed to add domain: \(error)"))
            } else if let message = response.message {
                notifications.add(.error(message))
            }
        } catch {
            notifications.add(.error("Failed to add domain: \(error.localizedDescription)"))
        }
    }

    func removeDomain(_ domain: String) async {
        do {
            let response: DomainRemoveResponse = try await bridge.call(
                "domains.remove",
                params: ["domain": domain]
            )
            if response.success {
                notifications.add(.success(response.message ?? "Domain removed"))
                await loadDomains()

                // Auto-regenerate if needed
                if response.needsCertRegen == true {
                    await regenerateCertificates()
                }
            } else if let error = response.error {
                notifications.add(.error("Failed to remove domain: \(error)"))
            } else if let message = response.message {
                notifications.add(.error(message))
            }
        } catch {
            notifications.add(.error("Failed to remove domain: \(error.localizedDescription)"))
        }
    }

    func regenerateCertificates() async {
        isRegeneratingCerts = true
        defer { isRegeneratingCerts = false }

        do {
            let response: RegenerateCertsResponse = try await bridge.call("domains.regenerate_certs")
            if response.success {
                let count = response.domainsCount ?? 0
                notifications.add(.success("Certificates regenerated for \(count) domains"))
                await loadDomains()
            } else if let error = response.error {
                notifications.add(.error("Failed to regenerate certificates: \(error)"))
            } else if let message = response.message {
                notifications.add(.error(message))
            }
        } catch {
            notifications.add(.error("Failed to regenerate certificates: \(error.localizedDescription)"))
        }
    }

    func updateHostsFile() async {
        do {
            let response: UpdateHostsResponse = try await bridge.call("domains.update_hosts")
            if response.success {
                let count = response.entriesAdded ?? 0
                if count > 0 {
                    notifications.add(.success("Added \(count) entries to hosts file"))
                } else {
                    notifications.add(.info(response.message ?? "No entries to add"))
                }
                await loadDomains()
            } else if let error = response.error {
                notifications.add(.error("Failed to update hosts: \(error)"))
            } else if let message = response.message {
                notifications.add(.error(message))
            }
        } catch {
            notifications.add(.error("Failed to update hosts file: \(error.localizedDescription)"))
        }
    }
}
