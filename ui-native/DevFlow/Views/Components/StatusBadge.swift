import SwiftUI

struct StatusBadge: View {
    let isRunning: Bool
    var size: Size = .medium

    enum Size {
        case small, medium, large

        var fontSize: Font {
            switch self {
            case .small: return .caption2
            case .medium: return .caption
            case .large: return .subheadline
            }
        }

        var padding: EdgeInsets {
            switch self {
            case .small: return EdgeInsets(top: 2, leading: 4, bottom: 2, trailing: 4)
            case .medium: return EdgeInsets(top: 3, leading: 6, bottom: 3, trailing: 6)
            case .large: return EdgeInsets(top: 4, leading: 8, bottom: 4, trailing: 8)
            }
        }
    }

    var body: some View {
        HStack(spacing: 4) {
            Circle()
                .fill(isRunning ? Color.green : Color.secondary)
                .frame(width: 6, height: 6)
            Text(isRunning ? "Running" : "Stopped")
                .font(size.fontSize)
        }
        .padding(size.padding)
        .background(isRunning ? Color.green.opacity(0.1) : Color.secondary.opacity(0.1))
        .foregroundStyle(isRunning ? .green : .secondary)
        .cornerRadius(4)
        .accessibilityIdentifier(isRunning ? "statusBadgeRunning" : "statusBadgeStopped")
    }
}

#Preview {
    VStack(spacing: 20) {
        StatusBadge(isRunning: true, size: .small)
        StatusBadge(isRunning: true, size: .medium)
        StatusBadge(isRunning: true, size: .large)

        StatusBadge(isRunning: false, size: .small)
        StatusBadge(isRunning: false, size: .medium)
        StatusBadge(isRunning: false, size: .large)
    }
    .padding()
}
