import SwiftUI

/// A compact status indicator showing AI availability.
struct AIStatusIndicator: View {
    @Environment(AppState.self) private var appState

    var isAvailable: Bool {
        appState.aiManager.isAvailable
    }

    var providerName: String? {
        appState.aiManager.activeProvider
    }

    var body: some View {
        HStack(spacing: 4) {
            Circle()
                .fill(statusColor)
                .frame(width: 6, height: 6)

            Text(statusText)
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
        .help(helpText)
    }

    private var statusColor: Color {
        if appState.aiManager.isProcessing {
            return .blue
        } else if isAvailable {
            return .green
        } else {
            return .orange
        }
    }

    private var statusText: String {
        if appState.aiManager.isProcessing {
            return "AI Working..."
        } else if isAvailable {
            return "AI Ready"
        } else {
            return "AI Limited"
        }
    }

    private var helpText: String {
        if let provider = providerName {
            return "Active provider: \(provider)"
        } else if isAvailable {
            return "AI features are available"
        } else {
            return "AI features are limited. Connect to an AI provider for full functionality."
        }
    }
}

/// A more detailed AI status view for settings or dialogs.
struct AIStatusDetailView: View {
    @Environment(AppState.self) private var appState

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header
            HStack {
                Image(systemName: "cpu")
                    .foregroundStyle(appState.aiManager.isAvailable ? .green : .orange)
                Text("AI Status")
                    .font(.headline)
                Spacer()
                AIStatusIndicator()
            }

            Divider()

            // Provider list
            if !appState.aiManager.providerStatuses.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Providers")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)

                    ForEach(appState.aiManager.providerStatuses) { provider in
                        HStack {
                            Image(systemName: provider.icon)
                                .frame(width: 20)
                            Text(provider.displayName)
                            Spacer()
                            if provider.isActive {
                                Text("Active")
                                    .font(.caption)
                                    .foregroundStyle(.green)
                            } else if provider.available {
                                Text("Available")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            } else {
                                Text("Unavailable")
                                    .font(.caption)
                                    .foregroundStyle(.tertiary)
                            }
                        }
                        .padding(.vertical, 2)
                    }
                }
            }

            // Embedding backend
            if let backend = appState.aiManager.embeddingBackend {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Embeddings")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)

                    HStack {
                        Image(systemName: "waveform")
                            .frame(width: 20)
                        Text(backend.capitalized)
                        Spacer()
                        Text("Active")
                            .font(.caption)
                            .foregroundStyle(.green)
                    }
                }
                .padding(.top, 4)
            }

            // Error message
            if let error = appState.aiManager.lastError {
                HStack {
                    Image(systemName: "exclamationmark.triangle")
                        .foregroundStyle(.orange)
                    Text(error)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                .padding(.top, 4)
            }
        }
        .padding()
        .task {
            await appState.aiManager.checkAvailability()
        }
    }
}

/// A button that shows AI status and opens a popover with details.
struct AIStatusButton: View {
    @Environment(AppState.self) private var appState
    @State private var showPopover = false

    var body: some View {
        Button {
            showPopover.toggle()
        } label: {
            HStack(spacing: 4) {
                Image(systemName: "cpu")
                    .font(.caption)
                Circle()
                    .fill(appState.aiManager.isAvailable ? .green : .orange)
                    .frame(width: 6, height: 6)
            }
        }
        .buttonStyle(.plain)
        .help("AI Status")
        .popover(isPresented: $showPopover, arrowEdge: .bottom) {
            AIStatusDetailView()
                .frame(width: 280)
        }
    }
}

#Preview {
    VStack(spacing: 20) {
        AIStatusIndicator()
        AIStatusButton()
    }
    .padding()
}
