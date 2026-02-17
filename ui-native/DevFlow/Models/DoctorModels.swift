import Foundation

// MARK: - Package Check Models

struct PackageCheck: Codable, Identifiable {
    let name: String
    let importName: String
    let status: String
    let version: String?
    let requiredFor: String
    let installCmd: String
    let error: String?

    var id: String { name }

    var isOk: Bool { status == "ok" }
    var isMissing: Bool { status == "missing" }
    var hasError: Bool { status == "error" }

    enum CodingKeys: String, CodingKey {
        case name
        case importName = "import_name"
        case status
        case version
        case requiredFor = "required_for"
        case installCmd = "install_cmd"
        case error
    }
}

struct PackageSummary: Codable {
    let total: Int
    let ok: Int
    let missing: Int
    let error: Int
}

// MARK: - Doctor Response Models

struct PackageDoctorResponse: Codable {
    let overallStatus: String
    let packages: [PackageCheck]
    let summary: PackageSummary
    let canAutoFix: Bool

    enum CodingKeys: String, CodingKey {
        case overallStatus = "overall_status"
        case packages
        case summary
        case canAutoFix = "can_auto_fix"
    }
}

struct ToolCheckDetails: Codable {
    let version: String?
    let authenticated: Bool?
}

struct ToolCheck: Codable, Identifiable {
    let name: String
    let category: String
    let status: String
    let message: String
    let fixHint: String?
    let details: ToolCheckDetails?

    var id: String { name }

    var isOk: Bool { status == "ok" }
    var isWarning: Bool { status == "warning" }
    var hasError: Bool { status == "error" }

    enum CodingKeys: String, CodingKey {
        case name
        case category
        case status
        case message
        case fixHint = "fix_hint"
        case details
    }
}

struct ToolsDoctorResponse: Codable {
    let overallStatus: String
    let checks: [ToolCheck]

    enum CodingKeys: String, CodingKey {
        case overallStatus = "overall_status"
        case checks
    }
}

struct FullDoctorResponse: Codable {
    let overallStatus: String
    let tools: ToolsDoctorResponse
    let packages: PackageDoctorResponse
    let canAutoFix: Bool

    enum CodingKeys: String, CodingKey {
        case overallStatus = "overall_status"
        case tools
        case packages
        case canAutoFix = "can_auto_fix"
    }
}

// MARK: - Install Response Models

struct PackageInstallResponse: Codable {
    let success: Bool
    let package: String?
    let version: String?
    let error: String?
    let output: String?

    enum CodingKeys: String, CodingKey {
        case success
        case package
        case version
        case error
        case output
    }
}

struct InstallAllResponse: Codable {
    let success: Bool
    let installed: [String]
    let failed: [FailedPackage]?
    let totalMissing: Int?
    let totalInstalled: Int?
    let message: String?

    enum CodingKeys: String, CodingKey {
        case success
        case installed
        case failed
        case totalMissing = "total_missing"
        case totalInstalled = "total_installed"
        case message
    }
}

struct FailedPackage: Codable {
    let package: String
    let error: String
}
