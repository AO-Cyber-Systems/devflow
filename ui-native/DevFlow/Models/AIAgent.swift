import Foundation

// MARK: - Agent Install Method

enum AgentInstallMethod: String, Codable, CaseIterable {
    case npm
    case curl
    case pip
    case brew
    case manual
    case vscode

    var displayName: String {
        switch self {
        case .npm: return "npm (Node.js)"
        case .curl: return "curl script"
        case .pip: return "pip (Python)"
        case .brew: return "Homebrew"
        case .manual: return "Manual"
        case .vscode: return "VS Code Extension"
        }
    }
}

// MARK: - Agent Capability

enum AgentCapability: String, Codable, CaseIterable {
    case codeGeneration = "code_generation"
    case codeEdit = "code_edit"
    case terminal
    case mcp
    case fileSearch = "file_search"
    case webSearch = "web_search"
    case multiFile = "multi_file"
    case git
    case testing
    case debugging

    var displayName: String {
        switch self {
        case .codeGeneration: return "Code Generation"
        case .codeEdit: return "Code Editing"
        case .terminal: return "Terminal Access"
        case .mcp: return "MCP Support"
        case .fileSearch: return "File Search"
        case .webSearch: return "Web Search"
        case .multiFile: return "Multi-file Editing"
        case .git: return "Git Integration"
        case .testing: return "Test Generation"
        case .debugging: return "Debugging"
        }
    }

    var icon: String {
        switch self {
        case .codeGeneration: return "doc.text"
        case .codeEdit: return "pencil"
        case .terminal: return "terminal"
        case .mcp: return "link"
        case .fileSearch: return "doc.text.magnifyingglass"
        case .webSearch: return "globe"
        case .multiFile: return "doc.on.doc"
        case .git: return "arrow.triangle.branch"
        case .testing: return "checkmark.circle"
        case .debugging: return "ladybug"
        }
    }
}

// MARK: - Agent Provider

enum AgentProvider: String, Codable, CaseIterable {
    case anthropic
    case openai
    case google
    case ollama
    case openrouter
    case azure
    case awsBedrock = "aws_bedrock"

    var displayName: String {
        switch self {
        case .anthropic: return "Anthropic (Claude)"
        case .openai: return "OpenAI"
        case .google: return "Google (Gemini)"
        case .ollama: return "Ollama (Local)"
        case .openrouter: return "OpenRouter"
        case .azure: return "Azure OpenAI"
        case .awsBedrock: return "AWS Bedrock"
        }
    }

    var apiKeyEnvVar: String {
        switch self {
        case .anthropic: return "ANTHROPIC_API_KEY"
        case .openai: return "OPENAI_API_KEY"
        case .google: return "GEMINI_API_KEY"
        case .ollama: return ""
        case .openrouter: return "OPENROUTER_API_KEY"
        case .azure: return "AZURE_OPENAI_API_KEY"
        case .awsBedrock: return "AWS_ACCESS_KEY_ID"
        }
    }
}

// MARK: - API Key Config

struct ApiKeyConfig: Codable, Identifiable {
    var id: String { provider }
    let provider: String
    let providerDisplay: String
    let envVar: String
    let required: Bool
    let description: String

    enum CodingKeys: String, CodingKey {
        case provider
        case providerDisplay = "provider_display"
        case envVar = "env_var"
        case required
        case description
    }
}

// MARK: - Capability Display Info

struct CapabilityDisplayInfo: Codable, Identifiable {
    var id: String { capabilityId }
    let capabilityId: String
    let name: String
    let icon: String

    enum CodingKeys: String, CodingKey {
        case capabilityId = "id"
        case name
        case icon
    }
}

// MARK: - Provider Display Info

struct ProviderDisplayInfo: Codable, Identifiable {
    var id: String { providerId }
    let providerId: String
    let name: String

    enum CodingKeys: String, CodingKey {
        case providerId = "id"
        case name
    }
}

// MARK: - AI Agent

struct AIAgent: Identifiable, Codable, Hashable {
    let id: String
    let name: String
    let description: String
    let homepage: String
    let installMethod: AgentInstallMethod
    let installMethodDisplay: String
    let installCommand: String
    let configLocation: String
    let capabilities: [String]
    let capabilitiesDisplay: [CapabilityDisplayInfo]
    let supportedProviders: [String]
    let supportedProvidersDisplay: [ProviderDisplayInfo]
    let apiKeys: [ApiKeyConfig]
    var isInstalled: Bool
    var isConfigured: Bool
    var installedVersion: String?
    let icon: String
    let version: String?
    let aliases: [String]
    let docsUrl: String?
    let githubUrl: String?

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case description
        case homepage
        case installMethod = "install_method"
        case installMethodDisplay = "install_method_display"
        case installCommand = "install_command"
        case configLocation = "config_location"
        case capabilities
        case capabilitiesDisplay = "capabilities_display"
        case supportedProviders = "supported_providers"
        case supportedProvidersDisplay = "supported_providers_display"
        case apiKeys = "api_keys"
        case isInstalled = "is_installed"
        case isConfigured = "is_configured"
        case installedVersion = "installed_version"
        case icon
        case version
        case aliases
        case docsUrl = "docs_url"
        case githubUrl = "github_url"
    }

    static func == (lhs: AIAgent, rhs: AIAgent) -> Bool {
        lhs.id == rhs.id
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
}

// MARK: - API Responses

struct AgentListResponse: Codable {
    let agents: [AIAgent]
    let total: Int
    let error: String?
}

struct AgentDetailResponse: Codable {
    let agent: AIAgent?
    let error: String?
}

struct AgentInstallResponse: Codable {
    let success: Bool
    let message: String?
    let output: String?
    let error: String?
}

struct AgentInstalledCheckResponse: Codable {
    let installed: [String: Bool]?
    let error: String?
}

struct AgentApiKeyConfigResponse: Codable {
    let success: Bool
    let message: String?
    let error: String?
}

struct AgentApiKeyStatusResponse: Codable {
    let agentId: String?
    let providers: [String: Bool]?
    let error: String?

    enum CodingKeys: String, CodingKey {
        case agentId = "agent_id"
        case providers
        case error
    }
}
