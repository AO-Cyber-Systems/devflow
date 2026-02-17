import Foundation

// MARK: - Domain Status

struct DomainStatus: Codable, Identifiable {
    var id: String { domain }

    let domain: String
    let inCertificate: Bool
    let inHostsFile: Bool
    let isWildcard: Bool
    let source: String

    var isDefault: Bool {
        source == "default"
    }

    var sourceDisplay: String {
        if source == "default" {
            return "Default"
        } else if source == "user" {
            return "User"
        } else if source.hasPrefix("project:") {
            return source.replacingOccurrences(of: "project:", with: "")
        }
        return source
    }

    enum CodingKeys: String, CodingKey {
        case domain
        case inCertificate = "in_certificate"
        case inHostsFile = "in_hosts_file"
        case isWildcard = "is_wildcard"
        case source
    }
}

// MARK: - Certificate Info

struct CertificateInfo: Codable {
    let valid: Bool
    let path: String
    let domains: [String]
    let expiresAt: String?
    let issuer: String?

    var expiresAtDate: Date? {
        guard let expiresAt = expiresAt else { return nil }
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let date = formatter.date(from: expiresAt) {
            return date
        }
        // Try without fractional seconds
        formatter.formatOptions = [.withInternetDateTime]
        return formatter.date(from: expiresAt)
    }

    var expiresAtFormatted: String {
        guard let date = expiresAtDate else { return "Unknown" }
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .none
        return formatter.string(from: date)
    }

    var domainsDisplay: String {
        domains.joined(separator: ", ")
    }

    static let empty = CertificateInfo(
        valid: false,
        path: "",
        domains: [],
        expiresAt: nil,
        issuer: nil
    )

    enum CodingKeys: String, CodingKey {
        case valid
        case path
        case domains
        case expiresAt = "expires_at"
        case issuer
    }
}

// MARK: - Domains List Response

struct DomainsListResponse: Codable {
    let domains: [DomainStatus]
    let certInfo: CertificateInfo
    let hostsEntries: [String]

    enum CodingKeys: String, CodingKey {
        case domains
        case certInfo = "cert_info"
        case hostsEntries = "hosts_entries"
    }
}

// MARK: - Domain Add Response

struct DomainAddResponse: Codable {
    let success: Bool
    let message: String?
    let needsCertRegen: Bool?
    let error: String?

    enum CodingKeys: String, CodingKey {
        case success
        case message
        case needsCertRegen = "needs_cert_regen"
        case error
    }
}

// MARK: - Domain Remove Response

struct DomainRemoveResponse: Codable {
    let success: Bool
    let message: String?
    let needsCertRegen: Bool?
    let error: String?

    enum CodingKeys: String, CodingKey {
        case success
        case message
        case needsCertRegen = "needs_cert_regen"
        case error
    }
}

// MARK: - Regenerate Certs Response

struct RegenerateCertsResponse: Codable {
    let success: Bool
    let message: String?
    let domainsCount: Int?
    let error: String?

    enum CodingKeys: String, CodingKey {
        case success
        case message
        case domainsCount = "domains_count"
        case error
    }
}

// MARK: - Update Hosts Response

struct UpdateHostsResponse: Codable {
    let success: Bool
    let message: String?
    let entriesAdded: Int?
    let error: String?

    enum CodingKeys: String, CodingKey {
        case success
        case message
        case entriesAdded = "entries_added"
        case error
    }
}
