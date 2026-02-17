import SwiftUI

/// Table view showing volume mounts for a project.
struct VolumesTableView: View {
    let volumes: [VolumeMount]

    var body: some View {
        if volumes.isEmpty {
            EmptyVolumesView()
        } else {
            VStack(spacing: 0) {
                // Header
                HStack {
                    Text("Service")
                        .frame(width: 80, alignment: .leading)
                    Text("Host Path")
                        .frame(maxWidth: .infinity, alignment: .leading)
                    Text("Container Path")
                        .frame(width: 150, alignment: .leading)
                    Text("Mode")
                        .frame(width: 50, alignment: .center)
                }
                .font(.caption)
                .fontWeight(.medium)
                .foregroundStyle(.secondary)
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(Color(nsColor: .controlBackgroundColor))

                Divider()

                // Rows
                ForEach(volumes) { volume in
                    VolumeRow(volume: volume)
                    if volume.id != volumes.last?.id {
                        Divider()
                            .padding(.leading, 12)
                    }
                }
            }
            .background(Color(nsColor: .textBackgroundColor))
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Color(nsColor: .separatorColor), lineWidth: 1)
            )
        }
    }
}

struct VolumeRow: View {
    let volume: VolumeMount

    var body: some View {
        HStack {
            Text(volume.service)
                .frame(width: 80, alignment: .leading)
                .lineLimit(1)

            HStack(spacing: 4) {
                Text(volume.hostPath)
                    .font(.system(.caption, design: .monospaced))
                    .lineLimit(1)
                    .truncationMode(.middle)

                if !volume.hostPath.starts(with: "/") {
                    // Named volume
                    Image(systemName: "cylinder")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)

            Text(volume.containerPath)
                .font(.system(.caption, design: .monospaced))
                .frame(width: 150, alignment: .leading)
                .lineLimit(1)

            Text(volume.isReadOnly ? "ro" : "rw")
                .font(.caption)
                .foregroundStyle(volume.isReadOnly ? .orange : .green)
                .frame(width: 50, alignment: .center)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .accessibilityIdentifier("volumeRow_\(volume.containerPath)")
    }
}

struct EmptyVolumesView: View {
    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: "externaldrive")
                .foregroundStyle(.secondary)
            Text("No volume mounts")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 16)
        .background(Color(nsColor: .controlBackgroundColor))
        .cornerRadius(8)
    }
}

#Preview {
    VolumesTableView(volumes: [
        VolumeMount(service: "web", hostPath: "./src", containerPath: "/app/src", mode: "rw"),
        VolumeMount(service: "db", hostPath: "postgres_data", containerPath: "/var/lib/postgresql/data", mode: "rw"),
        VolumeMount(service: "web", hostPath: "./config", containerPath: "/app/config", mode: "ro"),
    ])
    .padding()
    .frame(width: 600)
}
