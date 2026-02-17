import SwiftUI

struct NotificationBanner: View {
    let notification: AppNotification
    let onDismiss: () -> Void

    var backgroundColor: Color {
        switch notification.type {
        case .success: return .green
        case .error: return .red
        case .warning: return .orange
        case .info: return .blue
        }
    }

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: notification.type.icon)
                .font(.title3)

            Text(notification.message)
                .fontWeight(.medium)
                .lineLimit(2)

            Spacer()

            Button {
                onDismiss()
            } label: {
                Image(systemName: "xmark")
                    .font(.caption)
            }
            .buttonStyle(.plain)
            .accessibilityIdentifier("dismissNotificationButton")
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(backgroundColor.opacity(0.9))
        .foregroundStyle(.white)
        .cornerRadius(10)
        .shadow(color: .black.opacity(0.1), radius: 8, x: 0, y: 4)
        .accessibilityIdentifier("notificationBanner_\(notification.type)")
    }
}

struct NotificationOverlay: View {
    @Environment(AppState.self) private var appState

    var body: some View {
        VStack(alignment: .trailing, spacing: 8) {
            ForEach(appState.notifications) { notification in
                NotificationBanner(notification: notification) {
                    withAnimation {
                        appState.dismissNotification(notification)
                    }
                }
                .transition(.asymmetric(
                    insertion: .move(edge: .trailing).combined(with: .opacity),
                    removal: .move(edge: .trailing).combined(with: .opacity)
                ))
            }
        }
        .frame(maxWidth: 400)
        .animation(.spring(response: 0.3), value: appState.notifications.count)
        .accessibilityIdentifier("notificationOverlay")
    }
}

#Preview {
    VStack(spacing: 12) {
        NotificationBanner(
            notification: .success("Infrastructure started successfully"),
            onDismiss: {}
        )

        NotificationBanner(
            notification: .error("Failed to connect to Docker"),
            onDismiss: {}
        )

        NotificationBanner(
            notification: .warning("Traefik is using a non-standard port"),
            onDismiss: {}
        )

        NotificationBanner(
            notification: .info("New version available"),
            onDismiss: {}
        )
    }
    .padding()
}
