import SwiftUI

struct SecretsView: View {
    @Environment(AppState.self) private var appState
    @State private var searchText = ""

    var filteredSecrets: [Secret] {
        if searchText.isEmpty {
            return appState.secrets
        }
        return appState.secrets.filter {
            $0.key.localizedCaseInsensitiveContains(searchText)
        }
    }

    var body: some View {
        VStack(spacing: 0) {
            // Header - don't apply identifier here, apply to a wrapper instead
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Secrets")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                    Text("Manage environment variables and secrets")
                        .foregroundStyle(.secondary)
                }

                Spacer()

                Button {
                    appState.showAddSecret = true
                } label: {
                    Label("Add Secret", systemImage: "plus")
                }
                .buttonStyle(.borderedProminent)
                .accessibilityIdentifier("addSecretButton")
            }
            .padding(24)

            Divider()

            // Search
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundStyle(.secondary)
                TextField("Search secrets...", text: $searchText)
                    .textFieldStyle(.plain)
                    .accessibilityIdentifier("secretSearchField")
            }
            .padding(8)
            .background(Color(nsColor: .controlBackgroundColor))
            .cornerRadius(8)
            .padding(.horizontal, 24)
            .padding(.vertical, 12)

            // Secrets List
            if appState.isLoadingSecrets && appState.secrets.isEmpty {
                VStack {
                    Spacer()
                    ProgressView("Loading secrets...")
                    Spacer()
                }
            } else if filteredSecrets.isEmpty {
                VStack(spacing: 12) {
                    Spacer()
                    Image(systemName: searchText.isEmpty ? "key.fill" : "magnifyingglass")
                        .font(.system(size: 40))
                        .foregroundStyle(.secondary)
                    Text(searchText.isEmpty ? "No secrets" : "No matching secrets")
                        .font(.headline)
                    if searchText.isEmpty {
                        Text("Add secrets to manage environment variables")
                            .foregroundStyle(.secondary)
                        Button("Add Secret") {
                            appState.showAddSecret = true
                        }
                        .accessibilityIdentifier("emptyStateAddSecretButton")
                    }
                    Spacer()
                }
                .frame(maxWidth: .infinity)
            } else {
                List {
                    ForEach(filteredSecrets) { secret in
                        SecretRow(secret: secret)
                            .accessibilityIdentifier("secretRow_\(secret.key)")
                    }
                }
                .listStyle(.inset)
                .accessibilityIdentifier("secretsList")
            }
        }
        .background(Color(nsColor: .windowBackgroundColor))
        .accessibilityIdentifier("secretsView")
        .task {
            await appState.loadSecrets()
        }
    }
}

struct SecretRow: View {
    let secret: Secret
    @Environment(AppState.self) private var appState
    @State private var showValue = false
    @State private var showDeleteConfirmation = false

    var body: some View {
        HStack(spacing: 16) {
            // Provider icon
            Image(systemName: secret.provider.icon)
                .frame(width: 32, height: 32)
                .background(Color.blue.opacity(0.1))
                .foregroundStyle(.blue)
                .cornerRadius(6)

            // Key and value
            VStack(alignment: .leading, spacing: 4) {
                Text(secret.key)
                    .fontWeight(.medium)

                HStack {
                    if showValue, let value = secret.value {
                        Text(value)
                            .font(.system(.caption, design: .monospaced))
                            .textSelection(.enabled)
                    } else {
                        Text("••••••••")
                            .font(.caption)
                    }

                    Button {
                        showValue.toggle()
                    } label: {
                        Image(systemName: showValue ? "eye.slash" : "eye")
                            .font(.caption)
                    }
                    .buttonStyle(.borderless)
                    .accessibilityIdentifier("toggleSecretVisibility_\(secret.key)")
                }
                .foregroundStyle(.secondary)
            }

            Spacer()

            // Provider badge
            Text(secret.provider.displayName)
                .font(.caption)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(Color.secondary.opacity(0.1))
                .cornerRadius(4)

            // Delete button
            Button(role: .destructive) {
                showDeleteConfirmation = true
            } label: {
                Image(systemName: "trash")
            }
            .buttonStyle(.borderless)
            .accessibilityIdentifier("deleteSecret_\(secret.key)")
        }
        .padding(.vertical, 8)
        .confirmationDialog(
            "Delete Secret",
            isPresented: $showDeleteConfirmation,
            titleVisibility: .visible
        ) {
            Button("Delete", role: .destructive) {
                Task {
                    await appState.deleteSecret(secret)
                }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("Are you sure you want to delete the secret '\(secret.key)'?")
        }
    }
}

struct AddSecretSheet: View {
    @Environment(AppState.self) private var appState
    @Environment(\.dismiss) private var dismiss

    @State private var key = ""
    @State private var value = ""
    @State private var provider: SecretsProvider = .system

    var isValid: Bool {
        !key.trimmingCharacters(in: .whitespaces).isEmpty &&
        !value.isEmpty
    }

    var body: some View {
        ScrollView {
            VStack(spacing: 0) {
                // Header
                HStack {
                    Text("Add Secret")
                        .font(.headline)
                    Spacer()
                    Button {
                        dismiss()
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(.secondary)
                    }
                    .buttonStyle(.plain)
                    .accessibilityIdentifier("closeAddSecretButton")
                }
                .padding()

                Divider()

                // Form
                VStack(alignment: .leading, spacing: 16) {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Key")
                            .fontWeight(.medium)
                        TextField("SECRET_KEY", text: $key)
                            .textFieldStyle(.roundedBorder)
                            .accessibilityIdentifier("secretKeyField")
                    }

                    VStack(alignment: .leading, spacing: 6) {
                        Text("Value")
                            .fontWeight(.medium)
                        SecureField("Enter secret value", text: $value)
                            .textFieldStyle(.roundedBorder)
                            .accessibilityIdentifier("secretValueField")
                    }

                    VStack(alignment: .leading, spacing: 6) {
                        Text("Provider")
                            .fontWeight(.medium)
                        Picker("Provider", selection: $provider) {
                            ForEach(SecretsProvider.allCases) { p in
                                Label(p.displayName, systemImage: p.icon)
                                    .tag(p)
                            }
                        }
                        .pickerStyle(.segmented)
                        .accessibilityIdentifier("secretProviderPicker")
                    }
                }
                .padding()

                Spacer(minLength: 20)

                Divider()

                // Actions
                HStack {
                    Button("Cancel") {
                        dismiss()
                    }
                    .keyboardShortcut(.cancelAction)
                    .accessibilityIdentifier("cancelAddSecretButton")

                    Spacer()

                    Button("Save") {
                        Task {
                            await appState.addSecret(key: key, value: value, provider: provider)
                            dismiss()
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(!isValid)
                    .keyboardShortcut(.defaultAction)
                    .accessibilityIdentifier("saveSecretButton")
                }
                .padding()
            }
        }
        .frame(width: 400, height: 320)
        .accessibilityIdentifier("addSecretSheet")
    }
}

#Preview {
    SecretsView()
        .environment(AppState())
        .frame(width: 800, height: 600)
}
