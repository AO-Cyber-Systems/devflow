import SwiftUI

struct ApiKeyConfigSheet: View {
    let agent: AIAgent
    @Environment(\.dismiss) private var dismiss
    @Environment(AppState.self) private var appState

    @State private var apiKeyValues: [String: String] = [:]
    @State private var isSaving = false

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Text("Configure API keys for \(agent.name) to enable AI functionality.")
                        .foregroundStyle(.secondary)
                }

                ForEach(agent.apiKeys) { keyConfig in
                    Section(keyConfig.providerDisplay) {
                        SecureField("API Key", text: Binding(
                            get: { apiKeyValues[keyConfig.provider] ?? "" },
                            set: { apiKeyValues[keyConfig.provider] = $0 }
                        ))
                        .textFieldStyle(.roundedBorder)

                        if !keyConfig.description.isEmpty {
                            Text(keyConfig.description)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }

                        HStack {
                            Text("Environment Variable:")
                                .foregroundStyle(.secondary)
                            Text(keyConfig.envVar)
                                .font(.system(.body, design: .monospaced))
                        }
                        .font(.caption)

                        if keyConfig.required {
                            Label("Required", systemImage: "exclamationmark.circle")
                                .font(.caption)
                                .foregroundStyle(.red)
                        }
                    }
                }

                Section {
                    Text("API keys are stored securely in \(agent.configLocation)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .formStyle(.grouped)
            .navigationTitle("Configure API Keys")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }

                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        Task {
                            await saveApiKeys()
                        }
                    }
                    .disabled(isSaving || !hasValidKeys)
                }
            }
        }
        .frame(minWidth: 450, minHeight: 400)
    }

    private var hasValidKeys: Bool {
        // Check that at least one required key is filled
        for keyConfig in agent.apiKeys {
            if keyConfig.required {
                if let value = apiKeyValues[keyConfig.provider], !value.isEmpty {
                    return true
                }
            }
        }
        // Or any key is filled
        return apiKeyValues.values.contains { !$0.isEmpty }
    }

    private func saveApiKeys() async {
        isSaving = true
        defer { isSaving = false }

        for (provider, apiKey) in apiKeyValues where !apiKey.isEmpty {
            await appState.configureAgentApiKey(agent.id, provider: provider, apiKey: apiKey)
        }

        dismiss()
    }
}

#Preview {
    ApiKeyConfigSheet(
        agent: AIAgent(
            id: "aider",
            name: "Aider",
            description: "AI pair programming",
            homepage: "https://aider.chat",
            installMethod: .pip,
            installMethodDisplay: "pip (Python)",
            installCommand: "pip install aider-chat",
            configLocation: "~/.aider/",
            capabilities: [],
            capabilitiesDisplay: [],
            supportedProviders: ["anthropic", "openai"],
            supportedProvidersDisplay: [],
            apiKeys: [
                ApiKeyConfig(provider: "anthropic", providerDisplay: "Anthropic (Claude)", envVar: "ANTHROPIC_API_KEY", required: false, description: "API key from console.anthropic.com"),
                ApiKeyConfig(provider: "openai", providerDisplay: "OpenAI", envVar: "OPENAI_API_KEY", required: false, description: "API key from platform.openai.com"),
            ],
            isInstalled: true,
            isConfigured: false,
            installedVersion: nil,
            icon: "person.2",
            version: nil,
            aliases: [],
            docsUrl: nil,
            githubUrl: nil
        )
    )
    .environment(AppState())
}
