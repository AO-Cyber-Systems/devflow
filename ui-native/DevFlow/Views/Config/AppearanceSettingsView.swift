import SwiftUI

/// Appearance mode for the application.
enum AppearanceMode: String, CaseIterable, Identifiable {
    case system = "system"
    case light = "light"
    case dark = "dark"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .system: return "System"
        case .light: return "Light"
        case .dark: return "Dark"
        }
    }

    var icon: String {
        switch self {
        case .system: return "circle.lefthalf.filled"
        case .light: return "sun.max.fill"
        case .dark: return "moon.fill"
        }
    }

    var colorScheme: ColorScheme? {
        switch self {
        case .system: return nil
        case .light: return .light
        case .dark: return .dark
        }
    }
}

/// View for configuring appearance settings.
struct AppearanceSettingsView: View {
    @AppStorage("appearanceMode") private var appearanceMode: String = AppearanceMode.system.rawValue

    private var selectedMode: AppearanceMode {
        AppearanceMode(rawValue: appearanceMode) ?? .system
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Theme")
                .fontWeight(.medium)

            HStack(spacing: 12) {
                ForEach(AppearanceMode.allCases) { mode in
                    AppearanceOptionButton(
                        mode: mode,
                        isSelected: selectedMode == mode,
                        action: {
                            appearanceMode = mode.rawValue
                            applyAppearance(mode)
                        }
                    )
                }
            }

            Text("Choose how DevFlow appears on your screen")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }

    private func applyAppearance(_ mode: AppearanceMode) {
        guard let window = NSApplication.shared.windows.first else { return }

        switch mode {
        case .system:
            window.appearance = nil
        case .light:
            window.appearance = NSAppearance(named: .aqua)
        case .dark:
            window.appearance = NSAppearance(named: .darkAqua)
        }
    }
}

/// Individual appearance option button.
struct AppearanceOptionButton: View {
    let mode: AppearanceMode
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                ZStack {
                    RoundedRectangle(cornerRadius: 8)
                        .fill(previewBackground)
                        .frame(width: 80, height: 50)
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .strokeBorder(isSelected ? Color.accentColor : Color.clear, lineWidth: 2)
                        )

                    Image(systemName: mode.icon)
                        .font(.title2)
                        .foregroundStyle(previewForeground)
                }

                Text(mode.displayName)
                    .font(.caption)
                    .foregroundStyle(isSelected ? .primary : .secondary)
            }
        }
        .buttonStyle(.plain)
        .accessibilityIdentifier("appearance\(mode.rawValue.capitalized)Button")
    }

    private var previewBackground: Color {
        switch mode {
        case .system:
            return Color(nsColor: .windowBackgroundColor)
        case .light:
            return Color(white: 0.95)
        case .dark:
            return Color(white: 0.15)
        }
    }

    private var previewForeground: Color {
        switch mode {
        case .system:
            return .primary
        case .light:
            return .black
        case .dark:
            return .white
        }
    }
}

#Preview {
    AppearanceSettingsView()
        .padding()
        .frame(width: 400)
}
