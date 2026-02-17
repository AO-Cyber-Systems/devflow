import Foundation

struct Database: Identifiable, Codable, Hashable {
    let id: String
    var name: String
    var type: DatabaseType
    var host: String
    var port: Int
    var isRunning: Bool
    var connectionString: String?

    init(
        id: String = UUID().uuidString,
        name: String,
        type: DatabaseType,
        host: String = "localhost",
        port: Int,
        isRunning: Bool = false,
        connectionString: String? = nil
    ) {
        self.id = id
        self.name = name
        self.type = type
        self.host = host
        self.port = port
        self.isRunning = isRunning
        self.connectionString = connectionString
    }

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case type
        case host
        case port
        case isRunning = "is_running"
        case connectionString = "connection_string"
    }
}

enum DatabaseType: String, Codable, CaseIterable, Identifiable {
    case postgres
    case mysql
    case redis
    case mongodb

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .postgres: return "PostgreSQL"
        case .mysql: return "MySQL"
        case .redis: return "Redis"
        case .mongodb: return "MongoDB"
        }
    }

    var icon: String {
        switch self {
        case .postgres: return "cylinder.split.1x2"
        case .mysql: return "cylinder"
        case .redis: return "memorychip"
        case .mongodb: return "leaf"
        }
    }

    var defaultPort: Int {
        switch self {
        case .postgres: return 5432
        case .mysql: return 3306
        case .redis: return 6379
        case .mongodb: return 27017
        }
    }

    var color: String {
        switch self {
        case .postgres: return "blue"
        case .mysql: return "orange"
        case .redis: return "red"
        case .mongodb: return "green"
        }
    }
}

// MARK: - API Responses

struct DatabaseListResponse: Codable {
    let databases: [Database]
    let total: Int
}

