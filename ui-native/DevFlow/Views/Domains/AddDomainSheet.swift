import SwiftUI

struct AddDomainSheet: View {
    @Environment(AppState.self) private var appState
    @Environment(\.dismiss) private var dismiss

    @State private var domain = ""
    @State private var isAdding = false

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("Add Domain")
                    .font(.headline)
                Spacer()
                Button {
                    dismiss()
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundStyle(.secondary)
                }
                .buttonStyle(.plain)
            }
            .padding()

            Divider()

            // Content
            VStack(alignment: .leading, spacing: 16) {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Domain")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)

                    TextField("example.dev", text: $domain)
                        .textFieldStyle(.roundedBorder)
                        .accessibilityIdentifier("domainTextField")
                }

                // Examples
                VStack(alignment: .leading, spacing: 4) {
                    Text("Examples:")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)

                    VStack(alignment: .leading, spacing: 2) {
                        Text("myapp.dev")
                            .font(.system(.caption, design: .monospaced))
                        Text("*.myproject.local (wildcard)")
                            .font(.system(.caption, design: .monospaced))
                        Text("api.myapp.localhost")
                            .font(.system(.caption, design: .monospaced))
                    }
                    .foregroundStyle(.tertiary)
                }

                // Note
                HStack(spacing: 8) {
                    Image(systemName: "info.circle")
                        .foregroundStyle(.blue)
                    Text("Certificate will be regenerated after adding the domain.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                .padding(8)
                .background(Color.blue.opacity(0.1))
                .cornerRadius(6)
            }
            .padding()

            Divider()

            // Actions
            HStack {
                Button("Cancel") {
                    dismiss()
                }
                .keyboardShortcut(.cancelAction)

                Spacer()

                Button {
                    Task {
                        await addDomain()
                    }
                } label: {
                    if isAdding {
                        ProgressView()
                            .scaleEffect(0.7)
                    } else {
                        Text("Add Domain")
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(domain.trimmingCharacters(in: .whitespaces).isEmpty || isAdding)
                .keyboardShortcut(.defaultAction)
                .accessibilityIdentifier("addDomainButton")
            }
            .padding()
        }
        .frame(width: 400)
    }

    private func addDomain() async {
        let trimmedDomain = domain.trimmingCharacters(in: .whitespaces).lowercased()
        guard !trimmedDomain.isEmpty else { return }

        isAdding = true
        defer { isAdding = false }

        await appState.addDomain(trimmedDomain)
        dismiss()
    }
}

#Preview {
    AddDomainSheet()
        .environment(AppState())
}
