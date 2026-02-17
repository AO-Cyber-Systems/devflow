import Foundation

/// Represents a single log entry from a container or service.
struct LogEntry: Identifiable, Codable, Equatable {
    var id: String { "\(source)-\(timestamp ?? "none")-\(message.prefix(50))" }

    let timestamp: String?
    let message: String
    let level: LogLevel
    let source: String

    var timestampDate: Date? {
        guard let timestamp = timestamp else { return nil }
        return ISO8601DateFormatter().date(from: timestamp)
    }

    var timestampFormatted: String {
        guard let date = timestampDate else {
            return timestamp ?? ""
        }
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm:ss.SSS"
        return formatter.string(from: date)
    }
}

/// Log level for categorizing log entries.
enum LogLevel: String, Codable, CaseIterable {
    case debug
    case info
    case warning
    case error

    var color: String {
        switch self {
        case .debug: return "gray"
        case .info: return "blue"
        case .warning: return "orange"
        case .error: return "red"
        }
    }

    var icon: String {
        switch self {
        case .debug: return "ant"
        case .info: return "info.circle"
        case .warning: return "exclamationmark.triangle"
        case .error: return "xmark.circle"
        }
    }

    /// Severity order for filtering (higher = more severe)
    var severity: Int {
        switch self {
        case .debug: return 0
        case .info: return 1
        case .warning: return 2
        case .error: return 3
        }
    }
}

/// Represents a Docker container available for log viewing.
struct ContainerInfo: Identifiable, Codable, Equatable {
    var id: String
    let name: String
    let status: String
    let image: String

    var isRunning: Bool {
        status.lowercased().contains("up")
    }

    var shortId: String {
        String(id.prefix(12))
    }
}

// MARK: - Response Types

struct ContainersListResponse: Codable {
    let success: Bool?
    let containers: [ContainerInfo]
    let error: String?

    var isSuccess: Bool { success ?? (error == nil) }
}

struct LogsResponse: Codable {
    let success: Bool?
    let logs: [LogEntry]
    let container: String?
    let service: String?
    let count: Int?
    let error: String?

    var isSuccess: Bool { success ?? (error == nil) }
}
