import Foundation

/// Standard result wrapper for RPC operations.
/// Provides a consistent response format across all backend handlers.
struct OperationResult: Codable {
    let success: Bool
    let message: String?
    let data: AnyCodable?
    let error: String?

    /// Check if operation succeeded with optional message matching
    func isSuccess(withMessage containing: String? = nil) -> Bool {
        guard success else { return false }
        if let containing = containing {
            return message?.localizedCaseInsensitiveContains(containing) ?? false
        }
        return true
    }

    /// Get a user-friendly description of the result
    var displayMessage: String {
        if success {
            return message ?? "Operation completed successfully"
        } else {
            return error ?? "An unknown error occurred"
        }
    }
}
