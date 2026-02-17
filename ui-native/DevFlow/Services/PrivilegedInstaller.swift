import Foundation
import AppKit

/// Utility for running commands that require user interaction (like sudo password)
enum PrivilegedInstaller {

    enum InstallError: Error, LocalizedError {
        case scriptError(String)
        case cancelled
        case commandFailed(String)
        case homebrewNotFound
        case failedToCreateScript

        var errorDescription: String? {
            switch self {
            case .scriptError(let msg):
                return "Script error: \(msg)"
            case .cancelled:
                return "Installation cancelled by user"
            case .commandFailed(let msg):
                return "Command failed: \(msg)"
            case .homebrewNotFound:
                return "Homebrew not found. Please install Homebrew first."
            case .failedToCreateScript:
                return "Failed to create installation script"
            }
        }
    }

    /// Run a command in Terminal by creating a temporary script and opening it
    /// This avoids needing Automation permissions for AppleScript
    static func runInTerminal(command: String) async throws {
        // Create a temporary shell script
        let scriptContent = """
        #!/bin/bash
        \(command)
        echo ""
        echo "✅ Done! You can close this window."
        exec bash
        """

        let tempDir = FileManager.default.temporaryDirectory
        let scriptPath = tempDir.appendingPathComponent("devflow-install-\(UUID().uuidString).sh")

        do {
            try scriptContent.write(to: scriptPath, atomically: true, encoding: .utf8)
            // Make it executable
            try FileManager.default.setAttributes([.posixPermissions: 0o755], ofItemAtPath: scriptPath.path)
        } catch {
            throw InstallError.failedToCreateScript
        }

        // Open the script with Terminal
        let config = NSWorkspace.OpenConfiguration()
        config.activates = true

        let terminalURL = URL(fileURLWithPath: "/System/Applications/Utilities/Terminal.app")

        do {
            try await NSWorkspace.shared.open([scriptPath], withApplicationAt: terminalURL, configuration: config)
        } catch {
            throw InstallError.scriptError("Failed to open Terminal: \(error.localizedDescription)")
        }

        // Clean up the script after a delay (give Terminal time to read it)
        DispatchQueue.global().asyncAfter(deadline: .now() + 5) {
            try? FileManager.default.removeItem(at: scriptPath)
        }
    }

    /// Install Docker Desktop using Homebrew in Terminal
    static func installDocker() async throws {
        guard let brewPath = findHomebrew() else {
            throw InstallError.homebrewNotFound
        }

        let command = "\(brewPath) install --cask docker"
        try await runInTerminal(command: command)
    }

    /// Install a tool using Homebrew in Terminal
    static func installWithHomebrew(formula: String, isCask: Bool = false) async throws {
        guard let brewPath = findHomebrew() else {
            throw InstallError.homebrewNotFound
        }

        let caskFlag = isCask ? " --cask" : ""
        let command = "\(brewPath) install\(caskFlag) \(formula)"
        try await runInTerminal(command: command)
    }

    /// Open the Docker Desktop download page as a fallback
    static func openDockerDownloadPage() {
        if let url = URL(string: "https://www.docker.com/products/docker-desktop/") {
            NSWorkspace.shared.open(url)
        }
    }

    // MARK: - Private Helpers

    private static func findHomebrew() -> String? {
        let candidates = [
            "/opt/homebrew/bin/brew",
            "/usr/local/bin/brew"
        ]

        for candidate in candidates {
            if FileManager.default.fileExists(atPath: candidate) {
                return candidate
            }
        }
        return nil
    }
}
