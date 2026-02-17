import SwiftUI

struct StatCard: View {
    let title: String
    let value: String
    let icon: String
    var trend: Trend?
    var color: Color = .blue

    enum Trend {
        case up(String)
        case down(String)
        case neutral(String)

        var icon: String {
            switch self {
            case .up: return "arrow.up.right"
            case .down: return "arrow.down.right"
            case .neutral: return "minus"
            }
        }

        var color: Color {
            switch self {
            case .up: return .green
            case .down: return .red
            case .neutral: return .secondary
            }
        }

        var text: String {
            switch self {
            case .up(let text), .down(let text), .neutral(let text):
                return text
            }
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: icon)
                    .font(.title3)
                    .foregroundStyle(color)
                Spacer()
                if let trend = trend {
                    HStack(spacing: 2) {
                        Image(systemName: trend.icon)
                        Text(trend.text)
                    }
                    .font(.caption)
                    .foregroundStyle(trend.color)
                }
            }

            VStack(alignment: .leading, spacing: 2) {
                Text(value)
                    .font(.title)
                    .fontWeight(.bold)
                Text(title)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(nsColor: .controlBackgroundColor))
        .cornerRadius(12)
    }
}

#Preview {
    HStack(spacing: 16) {
        StatCard(
            title: "Active Projects",
            value: "12",
            icon: "folder.fill",
            trend: .up("2 new"),
            color: .blue
        )

        StatCard(
            title: "Running Services",
            value: "3",
            icon: "server.rack",
            trend: .neutral("stable"),
            color: .green
        )

        StatCard(
            title: "Secrets",
            value: "24",
            icon: "key.fill",
            color: .purple
        )
    }
    .padding()
}
