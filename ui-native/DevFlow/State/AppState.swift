import Foundation
import SwiftUI

/// Main application state coordinator that composes all focused state managers.
@Observable
@MainActor
class AppState {
    // MARK: - Composed State Managers

    let notificationManager: NotificationState
    let connectionManager: ConnectionState
    let infrastructureManager: InfrastructureState
    let projectsManager: ProjectsState
    let secretsManager: SecretsState
    let databasesManager: DatabaseState
    let templatesManager: TemplatesState
    let setupManager: SetupState
    let toolsManager: ToolBrowserState
    let configManager: ConfigState
    let logsManager: LogsState
    let agentsManager: AgentsState
    let docsManager: DocsState
    let componentsManager: ComponentsState
    let codeManager: CodeState
    let aiManager: AIState
    let doctorManager: DoctorState

    // MARK: - Services

    @ObservationIgnored private let rpcClient = RpcClient()
    @ObservationIgnored private var _bridge: PythonBridge?

    private var bridge: PythonBridge {
        if _bridge == nil {
            _bridge = PythonBridge(rpcClient: rpcClient)
        }
        return _bridge!
    }

    // MARK: - Convenience Accessors (for backward compatibility)

    // Connection
    var isConnected: Bool { connectionManager.isConnected }
    var connectionError: String? { connectionManager.connectionError }

    // Infrastructure
    var infraStatus: InfraStatus { infrastructureManager.infraStatus }
    var isLoadingInfra: Bool { infrastructureManager.isLoadingInfra }
    var domainStatuses: [DomainStatus] { infrastructureManager.domainStatuses }
    var certificateInfo: CertificateInfo { infrastructureManager.certificateInfo }
    var hostsEntries: [String] { infrastructureManager.hostsEntries }
    var isLoadingDomains: Bool { infrastructureManager.isLoadingDomains }
    var isRegeneratingCerts: Bool { infrastructureManager.isRegeneratingCerts }
    var showAddDomain: Bool {
        get { infrastructureManager.showAddDomain }
        set { infrastructureManager.showAddDomain = newValue }
    }
    var domainsNeedingHostsEntry: Int { infrastructureManager.domainsNeedingHostsEntry }

    // Projects
    var projects: [Project] { projectsManager.projects }
    var isLoadingProjects: Bool { projectsManager.isLoadingProjects }
    var showAddProject: Bool {
        get { projectsManager.showAddProject }
        set { projectsManager.showAddProject = newValue }
    }

    // Secrets
    var secrets: [Secret] { secretsManager.secrets }
    var isLoadingSecrets: Bool { secretsManager.isLoadingSecrets }
    var showAddSecret: Bool {
        get { secretsManager.showAddSecret }
        set { secretsManager.showAddSecret = newValue }
    }

    // Databases
    var databases: [Database] { databasesManager.databases }
    var isLoadingDatabases: Bool { databasesManager.isLoadingDatabases }
    var showAddDatabase: Bool {
        get { databasesManager.showAddDatabase }
        set { databasesManager.showAddDatabase = newValue }
    }

    // Templates
    var templates: [Template] { templatesManager.templates }
    var isLoadingTemplates: Bool { templatesManager.isLoadingTemplates }
    var showNewProjectWizard: Bool {
        get { templatesManager.showNewProjectWizard }
        set { templatesManager.showNewProjectWizard = newValue }
    }

    // Setup
    var setupWizardStatus: SetupWizardStatus? { setupManager.setupWizardStatus }
    var showSetupWizard: Bool {
        get { setupManager.showSetupWizard }
        set { setupManager.showSetupWizard = newValue }
    }
    var essentialTools: [ToolStatus] { setupManager.essentialTools }
    var recommendedTools: [ToolStatus] { setupManager.recommendedTools }
    var isLoadingTools: Bool { setupManager.isLoadingTools }

    // Tool Browser
    var browsableTools: [BrowsableTool] { toolsManager.browsableTools }
    var toolCategories: [ToolCategoryInfo] { toolsManager.toolCategories }
    var toolSources: [ToolSourceInfo] { toolsManager.toolSources }
    var toolSearchQuery: String {
        get { toolsManager.searchQuery }
        set { toolsManager.searchQuery = newValue }
    }
    var selectedToolSources: Set<ToolSource> {
        get { toolsManager.selectedSources }
        set { toolsManager.selectedSources = newValue }
    }
    var selectedToolCategories: Set<ToolBrowserCategory> {
        get { toolsManager.selectedCategories }
        set { toolsManager.selectedCategories = newValue }
    }
    var showInstalledToolsOnly: Bool {
        get { toolsManager.showInstalledOnly }
        set { toolsManager.showInstalledOnly = newValue }
    }
    var isLoadingBrowsableTools: Bool { toolsManager.isLoading }
    var toolsTotal: Int { toolsManager.total }
    var toolsHasMore: Bool { toolsManager.hasMore }
    var toolsOffset: Int { toolsManager.offset }
    var installingToolIds: Set<String> { toolsManager.installingToolIds }

    // Config
    var globalConfig: GlobalConfig {
        get { configManager.globalConfig }
        set { configManager.globalConfig = newValue }
    }
    var isLoadingConfig: Bool { configManager.isLoading }

    // Notifications (direct access for convenience)
    var notifications: [AppNotification] { notificationManager.notifications }

    // AI Agents
    var agents: [AIAgent] { agentsManager.agents }
    var isLoadingAgents: Bool { agentsManager.isLoading }
    var agentSearchQuery: String {
        get { agentsManager.searchQuery }
        set { agentsManager.searchQuery = newValue }
    }
    var showInstalledAgentsOnly: Bool {
        get { agentsManager.showInstalledOnly }
        set { agentsManager.showInstalledOnly = newValue }
    }
    var installingAgentIds: Set<String> { agentsManager.installingAgentIds }

    // Documentation
    var docs: [Documentation] { docsManager.docs }
    var docTypes: [DocTypeInfo] { docsManager.docTypes }
    var docFormats: [DocFormatInfo] { docsManager.docFormats }
    var isLoadingDocs: Bool { docsManager.isLoading }
    var docsSearchQuery: String {
        get { docsManager.searchQuery }
        set { docsManager.searchQuery = newValue }
    }
    var selectedDocType: String? {
        get { docsManager.selectedDocType }
        set { docsManager.selectedDocType = newValue }
    }

    // Components
    var components: [ComponentDoc] { componentsManager.components }
    var componentCategories: [ComponentCategoryInfo] { componentsManager.categories }
    var allComponentCategories: [ComponentCategoryInfo] { componentsManager.allCategories }
    var isLoadingComponents: Bool { componentsManager.isLoading }
    var isScanningComponents: Bool { componentsManager.isScanning }
    var componentSearchQuery: String {
        get { componentsManager.searchQuery }
        set { componentsManager.searchQuery = newValue }
    }
    var selectedComponentCategory: String? {
        get { componentsManager.selectedCategory }
        set { componentsManager.selectedCategory = newValue }
    }

    // Code
    var codeSearchResults: [CodeSearchResult] { codeManager.searchResults }
    var codeEntityTypes: [CodeEntityTypeInfo] { codeManager.entityTypes }
    var codeSupportedLanguages: [String] { codeManager.supportedLanguages }
    var isLoadingCode: Bool { codeManager.isLoading }
    var isScanningCode: Bool { codeManager.isScanning }
    var codeSearchQuery: String {
        get { codeManager.searchQuery }
        set { codeManager.searchQuery = newValue }
    }
    var codeScanStatus: ScanStatusInfo? { codeManager.scanStatus }
    var codeStats: CodeStats? { codeManager.codeStats }

    // AI
    var isAIAvailable: Bool { aiManager.isAvailable }
    var isAIProcessing: Bool { aiManager.isProcessing }
    var activeAIProvider: String? { aiManager.activeProvider }
    var aiProviders: [AIProviderStatus] { aiManager.providerStatuses }

    // Doctor
    var isDoctorHealthy: Bool { doctorManager.isHealthy }
    var doctorHasIssues: Bool { doctorManager.hasIssues }
    var isDoctorChecking: Bool { doctorManager.isChecking }
    var showDoctorSheet: Bool {
        get { doctorManager.showDoctorSheet }
        set { doctorManager.showDoctorSheet = newValue }
    }
    var missingPackages: [PackageCheck] { doctorManager.missingPackages }

    // MARK: - Initialization

    init() {
        let bridge = PythonBridge(rpcClient: rpcClient)
        self._bridge = bridge

        // Create notification state first (others depend on it)
        let notificationManager = NotificationState()
        self.notificationManager = notificationManager

        // Create state managers
        self.connectionManager = ConnectionState(bridge: bridge)
        self.infrastructureManager = InfrastructureState(bridge: bridge, notifications: notificationManager)
        self.projectsManager = ProjectsState(bridge: bridge, notifications: notificationManager)
        self.secretsManager = SecretsState(bridge: bridge, notifications: notificationManager)
        self.databasesManager = DatabaseState(bridge: bridge, notifications: notificationManager)
        self.templatesManager = TemplatesState(bridge: bridge, notifications: notificationManager)
        self.setupManager = SetupState(bridge: bridge, notifications: notificationManager)
        self.toolsManager = ToolBrowserState(bridge: bridge, notifications: notificationManager)
        self.configManager = ConfigState(bridge: bridge, notifications: notificationManager)
        self.logsManager = LogsState(bridge: bridge, notifications: notificationManager)
        self.agentsManager = AgentsState(bridge: bridge, notifications: notificationManager)
        self.docsManager = DocsState(bridge: bridge, notifications: notificationManager)
        self.componentsManager = ComponentsState(bridge: bridge, notifications: notificationManager)
        self.codeManager = CodeState(bridge: bridge, notifications: notificationManager)
        self.aiManager = AIState(bridge: bridge, notifications: notificationManager)
        self.doctorManager = DoctorState(bridge: bridge, notifications: notificationManager)

        // Set up cross-state dependencies
        self.templatesManager.setProjectsState(self.projectsManager)
    }

    // MARK: - Initialization Actions

    func initialize() async {
        await connectionManager.connect()

        if connectionManager.isConnected {
            // Run doctor check on startup
            await doctorManager.runFullDoctor()

            await loadDashboard()
        }
    }

    func reconnect() async {
        await connectionManager.reconnect()

        if connectionManager.isConnected {
            await loadDashboard()
        }
    }

    // MARK: - Dashboard

    func loadDashboard() async {
        async let infra: Void = infrastructureManager.refresh()
        async let proj: Void = projectsManager.load()
        async let conf: Void = configManager.load()

        _ = await (infra, proj, conf)
    }

    // MARK: - Convenience Methods (backward compatibility)

    // Infrastructure
    func refreshInfraStatus() async { await infrastructureManager.refresh() }
    func startInfrastructure() async { await infrastructureManager.start() }
    func stopInfrastructure() async { await infrastructureManager.stop() }
    func loadDomains() async { await infrastructureManager.loadDomains() }
    func addDomain(_ domain: String, source: String = "user") async { await infrastructureManager.addDomain(domain, source: source) }
    func removeDomain(_ domain: String) async { await infrastructureManager.removeDomain(domain) }
    func regenerateCertificates() async { await infrastructureManager.regenerateCertificates() }
    func updateHostsFile() async { await infrastructureManager.updateHostsFile() }

    // Projects
    func loadProjects() async { await projectsManager.load() }
    func addProject(path: String) async { await projectsManager.add(path: path) }
    func removeProject(_ project: Project) async { await projectsManager.remove(project) }
    func startProject(_ project: Project) async { await projectsManager.start(project) }
    func stopProject(_ project: Project) async { await projectsManager.stop(project) }
    func updateProject(_ project: Project, domain: String?, port: Int?, commands: ProjectCommands?) async {
        await projectsManager.update(project, domain: domain, port: port, commands: commands)
    }
    func getProjectDetail(path: String) async throws -> ProjectDetail {
        try await projectsManager.getDetail(path: path)
    }

    // Secrets
    func loadSecrets() async { await secretsManager.load() }
    func addSecret(key: String, value: String, provider: SecretsProvider) async { await secretsManager.add(key: key, value: value, provider: provider) }
    func deleteSecret(_ secret: Secret) async { await secretsManager.delete(secret) }

    // Databases
    func loadDatabases() async { await databasesManager.load() }
    func createDatabase(name: String, type: DatabaseType) async { await databasesManager.create(name: name, type: type) }
    func deleteDatabase(_ database: Database) async { await databasesManager.delete(database) }
    func startDatabase(_ database: Database) async { await databasesManager.start(database) }
    func stopDatabase(_ database: Database) async { await databasesManager.stop(database) }

    // Config
    func loadConfig() async { await configManager.load() }
    func saveConfig() async { await configManager.save() }

    // Templates
    func loadTemplates(category: String? = nil, search: String? = nil) async { await templatesManager.load(category: category, search: search) }
    func loadTemplateDetail(_ templateId: String) async -> TemplateDetail? { await templatesManager.loadDetail(templateId) }
    func checkRequiredTools(_ templateId: String) async -> ToolCheckResponse? { await templatesManager.checkRequiredTools(templateId) }
    func createProject(templateId: String, values: [String: String]) async -> CreateProjectResponse? {
        await templatesManager.createProject(templateId: templateId, values: values)
    }
    func importTemplate(gitUrl: String, branch: String?, subdirectory: String?) async -> ImportTemplateResponse? {
        await templatesManager.importTemplate(gitUrl: gitUrl, branch: branch, subdirectory: subdirectory)
    }
    func removeTemplate(_ templateId: String) async { await templatesManager.remove(templateId) }

    // Setup
    func checkSetupWizardStatus() async { await setupManager.checkStatus() }
    func markSetupCompleted() async { await setupManager.markCompleted() }
    func loadEssentialTools() async { await setupManager.loadEssentialTools() }
    func loadRecommendedTools() async { await setupManager.loadRecommendedTools() }
    func installTool(_ toolId: String) async { await setupManager.install(toolId) }
    func installMultipleTools(_ toolIds: [String]) async { await setupManager.installMultiple(toolIds) }

    // Tool Browser
    func searchBrowsableTools(reset: Bool = true) async { await toolsManager.search(reset: reset) }
    func loadMoreBrowsableTools() async { await toolsManager.loadMore() }
    func loadToolCategories() async { await toolsManager.loadCategories() }
    func loadToolSources() async { await toolsManager.loadSources() }
    func refreshToolCache(force: Bool = true) async { await toolsManager.refreshCache(force: force) }
    func installBrowsableTool(_ toolId: String) async { await toolsManager.install(toolId) }
    func detectBrowsableToolsInstalled(_ toolIds: [String]) async { await toolsManager.detectInstalled(toolIds) }

    // Notifications
    func addNotification(_ notification: AppNotification) { notificationManager.add(notification) }
    func dismissNotification(_ notification: AppNotification) { notificationManager.dismiss(notification) }

    // AI Agents
    func loadAgents() async { await agentsManager.load() }
    func refreshAgents() async { await agentsManager.refresh() }
    func installAgent(_ agentId: String) async { await agentsManager.install(agentId) }
    func configureAgentApiKey(_ agentId: String, provider: String, apiKey: String) async {
        await agentsManager.configureApiKey(agentId, provider: provider, apiKey: apiKey)
    }

    // Documentation
    func loadDocs(projectPath: String? = nil) async { await docsManager.load(projectPath: projectPath) }
    func loadDocTypes() async { await docsManager.loadDocTypes() }
    func loadDocFormats() async { await docsManager.loadDocFormats() }
    func getDoc(_ docId: String, projectPath: String? = nil) async -> Documentation? {
        await docsManager.getDoc(docId, projectPath: projectPath)
    }
    func createDoc(
        title: String,
        content: String,
        docType: String,
        format: String,
        projectPath: String? = nil,
        description: String = "",
        tags: [String] = [],
        aiContext: String? = nil,
        autoSummarize: Bool = false,
        autoTag: Bool = false
    ) async -> Documentation? {
        await docsManager.createDoc(
            title: title,
            content: content,
            docType: docType,
            format: format,
            projectPath: projectPath,
            description: description,
            tags: tags,
            aiContext: aiContext,
            autoSummarize: autoSummarize,
            autoTag: autoTag
        )
    }
    func updateDoc(
        docId: String,
        projectPath: String? = nil,
        title: String? = nil,
        content: String? = nil,
        docType: String? = nil,
        format: String? = nil,
        description: String? = nil,
        tags: [String]? = nil,
        aiContext: String? = nil
    ) async -> Documentation? {
        await docsManager.updateDoc(
            docId: docId,
            projectPath: projectPath,
            title: title,
            content: content,
            docType: docType,
            format: format,
            description: description,
            tags: tags,
            aiContext: aiContext
        )
    }
    func deleteDoc(_ docId: String, projectPath: String? = nil) async {
        await docsManager.deleteDoc(docId, projectPath: projectPath)
    }
    func importDocFromFile(
        filePath: String,
        projectPath: String? = nil,
        docType: String = "custom",
        aiContext: String? = nil,
        autoSummarize: Bool = false,
        autoTag: Bool = false
    ) async -> Documentation? {
        await docsManager.importFromFile(
            filePath: filePath,
            projectPath: projectPath,
            docType: docType,
            aiContext: aiContext,
            autoSummarize: autoSummarize,
            autoTag: autoTag
        )
    }

    // Components
    func loadComponents(projectPath: String) async { await componentsManager.load(projectPath: projectPath) }
    func loadComponentCategories(projectPath: String) async { await componentsManager.loadCategories(projectPath: projectPath) }
    func loadAllComponentCategories() async { await componentsManager.loadAllCategories() }
    func createComponent(
        projectPath: String,
        name: String,
        category: String,
        description: String,
        aiGuidance: String? = nil,
        accessibility: [String]? = nil,
        tags: [String]? = nil
    ) async -> ComponentDoc? {
        await componentsManager.createComponent(
            projectPath: projectPath,
            name: name,
            category: category,
            description: description,
            aiGuidance: aiGuidance,
            accessibility: accessibility,
            tags: tags
        )
    }
    func updateComponent(
        projectPath: String,
        name: String,
        category: String? = nil,
        description: String? = nil,
        aiGuidance: String? = nil,
        accessibility: [String]? = nil,
        tags: [String]? = nil
    ) async -> ComponentDoc? {
        await componentsManager.updateComponent(
            projectPath: projectPath,
            name: name,
            category: category,
            description: description,
            aiGuidance: aiGuidance,
            accessibility: accessibility,
            tags: tags
        )
    }
    func deleteComponent(_ name: String, projectPath: String) async {
        await componentsManager.deleteComponent(name, projectPath: projectPath)
    }
    func scanComponents(projectPath: String, save: Bool = false) async -> [ComponentDoc] {
        await componentsManager.scanComponents(projectPath: projectPath, save: save)
    }

    // Code
    func scanCode(projectPath: String, languages: [String]? = nil) async -> ScanResult? {
        await codeManager.scanProject(path: projectPath, languages: languages)
    }
    func searchCode(query: String, projectPath: String? = nil, entityTypes: [String]? = nil, limit: Int = 20) async {
        await codeManager.search(query: query, projectPath: projectPath, entityTypes: entityTypes, limit: limit)
    }
    func listCodeEntities(projectPath: String, entityTypes: [String]? = nil, limit: Int = 100) async {
        await codeManager.listEntities(projectPath: projectPath, entityTypes: entityTypes, limit: limit)
    }
    func findFunction(name: String, projectPath: String? = nil) async -> [FunctionEntity] {
        await codeManager.findFunction(name: name, projectPath: projectPath)
    }
    func findClass(name: String, projectPath: String? = nil) async -> [ClassEntity] {
        await codeManager.findClass(name: name, projectPath: projectPath)
    }
    func getCodeStats(projectPath: String) async { await codeManager.getCodeStats(path: projectPath) }
    func getCodeScanStatus(projectPath: String) async { await codeManager.getScanStatus(path: projectPath) }
    func getCallers(entityId: String, projectPath: String? = nil) async -> [CodeEntity] {
        await codeManager.getCallers(entityId: entityId, projectPath: projectPath)
    }
    func getCallees(entityId: String, projectPath: String? = nil) async -> [CodeEntity] {
        await codeManager.getCallees(entityId: entityId, projectPath: projectPath)
    }
    func loadCodeEntityTypes() async { await codeManager.loadEntityTypes() }
    func loadCodeSupportedLanguages() async { await codeManager.loadSupportedLanguages() }

    // Web Fetch
    func importDocFromUrl(
        url: String,
        projectPath: String? = nil,
        docType: String = "reference",
        title: String? = nil
    ) async -> Documentation? {
        await docsManager.importFromUrl(url: url, projectPath: projectPath, docType: docType, title: title)
    }
    func importDocsSite(
        url: String,
        projectPath: String? = nil,
        docType: String = "reference",
        maxPages: Int = 50,
        maxDepth: Int = 3,
        pathPrefix: String? = nil
    ) async -> ImportDocsSiteResponse? {
        await docsManager.importDocsSite(
            url: url,
            projectPath: projectPath,
            docType: docType,
            maxPages: maxPages,
            maxDepth: maxDepth,
            pathPrefix: pathPrefix
        )
    }

    // MARK: - AI Methods

    func checkAIStatus() async { await aiManager.checkAvailability() }

    func summarizeContent(_ content: String, maxLength: Int = 500) async -> DocumentSummary? {
        await aiManager.summarize(content, maxLength: maxLength)
    }

    func summarizeDoc(_ docId: String, projectPath: String? = nil) async -> DocumentSummary? {
        await aiManager.summarizeDoc(docId, projectPath: projectPath)
    }

    func extractEntities(_ content: String) async -> ExtractedEntities? {
        await aiManager.extractEntities(content)
    }

    func extractDocEntities(_ docId: String, projectPath: String? = nil) async -> ExtractedEntities? {
        await aiManager.extractDocEntities(docId, projectPath: projectPath)
    }

    func explainCode(_ code: String, language: String, detailLevel: String = "basic") async -> CodeExplanation? {
        await aiManager.explainCode(code, language: language, detailLevel: detailLevel)
    }

    func explainCodeEntity(_ entityId: String, projectPath: String, detailLevel: String = "basic") async -> CodeExplanation? {
        await aiManager.explainEntity(entityId, projectPath: projectPath, detailLevel: detailLevel)
    }

    func generateTags(_ content: String, maxTags: Int = 10) async -> [String] {
        await aiManager.generateTags(content, maxTags: maxTags)
    }

    func generateDocstring(_ code: String, language: String) async -> String? {
        await aiManager.generateDocstring(code, language: language)
    }

    func generateEntityDocstring(_ entityId: String, projectPath: String) async -> String? {
        await aiManager.generateEntityDocstring(entityId, projectPath: projectPath)
    }

    func suggestCodeImprovements(_ code: String, language: String) async -> [String] {
        await aiManager.suggestImprovements(code, language: language)
    }

    func suggestEntityImprovements(_ entityId: String, projectPath: String) async -> [String] {
        await aiManager.suggestEntityImprovements(entityId, projectPath: projectPath)
    }

    func findSimilarCode(_ entityId: String, projectPath: String, limit: Int = 5) async -> [SimilarCodeResult] {
        await aiManager.findSimilarCode(entityId, projectPath: projectPath, limit: limit)
    }

    func suggestRelatedDocs(_ docId: String, projectPath: String? = nil) async -> [RelatedDocSuggestion] {
        await aiManager.suggestRelatedDocs(docId, projectPath: projectPath)
    }

    func autoEnhanceDoc(_ docId: String, projectPath: String? = nil, generateSummary: Bool = true, generateTags: Bool = true) async -> EnhancedDocInfo? {
        await aiManager.autoEnhanceDoc(docId, projectPath: projectPath, generateSummary: generateSummary, generateTags: generateTags)
    }

    // MARK: - Doctor Methods

    func runDoctorCheck() async { await doctorManager.runFullDoctor() }

    func installPackage(_ packageName: String) async -> Bool {
        await doctorManager.installPackage(packageName)
    }

    func installAllMissingPackages() async {
        await doctorManager.installAllMissing()
    }
}
