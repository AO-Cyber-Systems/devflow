import Foundation

/// Manages AI-powered features across DevFlow.
/// Provides summarization, entity extraction, code explanation, and more.
@Observable
@MainActor
class AIState {
    // MARK: - State

    var isAvailable = false
    var isProcessing = false
    var activeProvider: String?
    var providerStatuses: [AIProviderStatus] = []
    var embeddingBackend: String?
    var lastError: String?

    // Cached results
    var lastSummary: DocumentSummary?
    var lastEntities: ExtractedEntities?
    var lastExplanation: CodeExplanation?

    // MARK: - Dependencies

    @ObservationIgnored private let bridge: PythonBridge
    @ObservationIgnored private let notifications: NotificationState

    // MARK: - Initialization

    init(bridge: PythonBridge, notifications: NotificationState) {
        self.bridge = bridge
        self.notifications = notifications
    }

    // MARK: - Status

    func checkAvailability() async {
        do {
            let response: AIStatusResponse = try await bridge.call("ai.get_ai_status")

            isAvailable = response.available
            activeProvider = response.activeProvider
            embeddingBackend = response.embeddings?.activeBackend

            // Build provider statuses
            if let providers = response.providers {
                providerStatuses = providers.map { key, available in
                    AIProviderStatus(
                        id: key,
                        name: key,
                        available: available,
                        isActive: key == activeProvider
                    )
                }.sorted { $0.available && !$1.available }
            }

            if let error = response.error {
                lastError = error
            }
        } catch {
            isAvailable = false
            lastError = error.localizedDescription
        }
    }

    // MARK: - Summarization

    func summarize(_ content: String, maxLength: Int = 500) async -> DocumentSummary? {
        isProcessing = true
        defer { isProcessing = false }

        do {
            let params: [String: any Sendable] = [
                "content": content,
                "max_length": maxLength,
            ]

            let response: SummarizeResponse = try await bridge.call("ai.summarize", params: params)

            if response.success {
                let summary = DocumentSummary(from: response)
                lastSummary = summary
                return summary
            } else if let error = response.error {
                lastError = error
                notifications.add(.error("Summarization failed: \(error)"))
            }
        } catch {
            lastError = error.localizedDescription
            notifications.add(.error("Summarization failed: \(error.localizedDescription)"))
        }
        return nil
    }

    func summarizeDoc(_ docId: String, projectPath: String? = nil, maxLength: Int = 500) async -> DocumentSummary? {
        isProcessing = true
        defer { isProcessing = false }

        do {
            var params: [String: any Sendable] = [
                "doc_id": docId,
                "max_length": maxLength,
            ]
            if let path = projectPath {
                params["project_path"] = path
            }

            let response: SummarizeDocResponse = try await bridge.call("ai.summarize_doc", params: params)

            if response.success {
                let summary = DocumentSummary(from: SummarizeResponse(
                    success: true,
                    title: response.title,
                    keyPoints: response.keyPoints,
                    summary: response.summary,
                    error: nil
                ))
                lastSummary = summary
                return summary
            } else if let error = response.error {
                lastError = error
                notifications.add(.error("Summarization failed: \(error)"))
            }
        } catch {
            lastError = error.localizedDescription
            notifications.add(.error("Summarization failed: \(error.localizedDescription)"))
        }
        return nil
    }

    // MARK: - Entity Extraction

    func extractEntities(_ content: String) async -> ExtractedEntities? {
        isProcessing = true
        defer { isProcessing = false }

        do {
            let params: [String: any Sendable] = ["content": content]
            let response: ExtractEntitiesResponse = try await bridge.call("ai.extract_entities", params: params)

            if response.success {
                let entities = ExtractedEntities(from: response)
                lastEntities = entities
                return entities
            } else if let error = response.error {
                lastError = error
                notifications.add(.error("Entity extraction failed: \(error)"))
            }
        } catch {
            lastError = error.localizedDescription
            notifications.add(.error("Entity extraction failed: \(error.localizedDescription)"))
        }
        return nil
    }

    func extractDocEntities(_ docId: String, projectPath: String? = nil) async -> ExtractedEntities? {
        isProcessing = true
        defer { isProcessing = false }

        do {
            var params: [String: any Sendable] = ["doc_id": docId]
            if let path = projectPath {
                params["project_path"] = path
            }

            let response: ExtractDocEntitiesResponse = try await bridge.call("ai.extract_doc_entities", params: params)

            if response.success {
                let entities = ExtractedEntities(from: ExtractEntitiesResponse(
                    success: true,
                    apis: response.apis,
                    components: response.components,
                    concepts: response.concepts,
                    suggestedTags: response.suggestedTags,
                    error: nil
                ))
                lastEntities = entities
                return entities
            } else if let error = response.error {
                lastError = error
                notifications.add(.error("Entity extraction failed: \(error)"))
            }
        } catch {
            lastError = error.localizedDescription
            notifications.add(.error("Entity extraction failed: \(error.localizedDescription)"))
        }
        return nil
    }

    // MARK: - Code Explanation

    func explainCode(_ code: String, language: String, detailLevel: String = "basic") async -> CodeExplanation? {
        isProcessing = true
        defer { isProcessing = false }

        do {
            let params: [String: any Sendable] = [
                "code": code,
                "language": language,
                "detail_level": detailLevel,
            ]

            let response: ExplainCodeResponse = try await bridge.call("ai.explain_code", params: params)

            if response.success {
                let explanation = CodeExplanation(from: response)
                lastExplanation = explanation
                return explanation
            } else if let error = response.error {
                lastError = error
                notifications.add(.error("Code explanation failed: \(error)"))
            }
        } catch {
            lastError = error.localizedDescription
            notifications.add(.error("Code explanation failed: \(error.localizedDescription)"))
        }
        return nil
    }

    func explainEntity(_ entityId: String, projectPath: String, detailLevel: String = "basic") async -> CodeExplanation? {
        isProcessing = true
        defer { isProcessing = false }

        do {
            let params: [String: any Sendable] = [
                "entity_id": entityId,
                "project_path": projectPath,
                "detail_level": detailLevel,
            ]

            let response: ExplainCodeResponse = try await bridge.call("code.explain_entity", params: params)

            if response.success {
                let explanation = CodeExplanation(from: response)
                lastExplanation = explanation
                return explanation
            } else if let error = response.error {
                lastError = error
                notifications.add(.error("Code explanation failed: \(error)"))
            }
        } catch {
            lastError = error.localizedDescription
            notifications.add(.error("Code explanation failed: \(error.localizedDescription)"))
        }
        return nil
    }

    // MARK: - Tag Generation

    func generateTags(_ content: String, maxTags: Int = 10) async -> [String] {
        isProcessing = true
        defer { isProcessing = false }

        do {
            let params: [String: any Sendable] = [
                "content": content,
                "max_tags": maxTags,
            ]

            let response: GenerateTagsResponse = try await bridge.call("ai.generate_tags", params: params)

            if response.success, let tags = response.tags {
                return tags
            } else if let error = response.error {
                lastError = error
            }
        } catch {
            lastError = error.localizedDescription
        }
        return []
    }

    // MARK: - Query Expansion

    func expandQuery(_ query: String, context: String = "") async -> String {
        do {
            let params: [String: any Sendable] = [
                "query": query,
                "context": context,
            ]

            let response: ExpandQueryResponse = try await bridge.call("ai.expand_query", params: params)

            if response.success, let expanded = response.expandedQuery {
                return expanded
            }
        } catch {
            // Silent fail - return original query
        }
        return query
    }

    // MARK: - Docstring Generation

    func generateDocstring(_ code: String, language: String) async -> String? {
        isProcessing = true
        defer { isProcessing = false }

        do {
            let params: [String: any Sendable] = [
                "code": code,
                "language": language,
            ]

            let response: GenerateDocstringResponse = try await bridge.call("ai.generate_docstring", params: params)

            if response.success, let docstring = response.docstring {
                return docstring
            } else if let error = response.error {
                lastError = error
                notifications.add(.error("Docstring generation failed: \(error)"))
            }
        } catch {
            lastError = error.localizedDescription
            notifications.add(.error("Docstring generation failed: \(error.localizedDescription)"))
        }
        return nil
    }

    func generateEntityDocstring(_ entityId: String, projectPath: String) async -> String? {
        isProcessing = true
        defer { isProcessing = false }

        do {
            let params: [String: any Sendable] = [
                "entity_id": entityId,
                "project_path": projectPath,
            ]

            let response: GenerateDocstringResponse = try await bridge.call("code.generate_docstring", params: params)

            if response.success, let docstring = response.docstring {
                return docstring
            } else if let error = response.error {
                lastError = error
                notifications.add(.error("Docstring generation failed: \(error)"))
            }
        } catch {
            lastError = error.localizedDescription
            notifications.add(.error("Docstring generation failed: \(error.localizedDescription)"))
        }
        return nil
    }

    // MARK: - Improvement Suggestions

    func suggestImprovements(_ code: String, language: String) async -> [String] {
        isProcessing = true
        defer { isProcessing = false }

        do {
            let params: [String: any Sendable] = [
                "code": code,
                "language": language,
            ]

            let response: SuggestImprovementsResponse = try await bridge.call("ai.suggest_improvements", params: params)

            if response.success, let suggestions = response.suggestions {
                return suggestions
            } else if let error = response.error {
                lastError = error
            }
        } catch {
            lastError = error.localizedDescription
        }
        return []
    }

    func suggestEntityImprovements(_ entityId: String, projectPath: String) async -> [String] {
        isProcessing = true
        defer { isProcessing = false }

        do {
            let params: [String: any Sendable] = [
                "entity_id": entityId,
                "project_path": projectPath,
            ]

            let response: SuggestImprovementsResponse = try await bridge.call("code.suggest_improvements", params: params)

            if response.success, let suggestions = response.suggestions {
                return suggestions
            } else if let error = response.error {
                lastError = error
            }
        } catch {
            lastError = error.localizedDescription
        }
        return []
    }

    // MARK: - Similar Code

    func findSimilarCode(_ entityId: String, projectPath: String, limit: Int = 5) async -> [SimilarCodeResult] {
        isProcessing = true
        defer { isProcessing = false }

        do {
            let params: [String: any Sendable] = [
                "entity_id": entityId,
                "project_path": projectPath,
                "limit": limit,
            ]

            let response: FindSimilarCodeResponse = try await bridge.call("code.find_similar_code", params: params)

            if response.success, let similar = response.similar {
                return similar
            } else if let error = response.error {
                lastError = error
            }
        } catch {
            lastError = error.localizedDescription
        }
        return []
    }

    // MARK: - Related Documents

    func suggestRelatedDocs(_ docId: String, projectPath: String? = nil, limit: Int = 5) async -> [RelatedDocSuggestion] {
        isProcessing = true
        defer { isProcessing = false }

        do {
            var params: [String: any Sendable] = [
                "doc_id": docId,
                "limit": limit,
            ]
            if let path = projectPath {
                params["project_path"] = path
            }

            let response: SuggestRelatedDocsResponse = try await bridge.call("docs.suggest_related_docs", params: params)

            if response.success, let suggestions = response.suggestions {
                return suggestions
            } else if let error = response.error {
                lastError = error
            }
        } catch {
            lastError = error.localizedDescription
        }
        return []
    }

    // MARK: - Auto Enhance

    func autoEnhanceDoc(_ docId: String, projectPath: String? = nil, generateSummary: Bool = true, generateTags: Bool = true) async -> EnhancedDocInfo? {
        isProcessing = true
        defer { isProcessing = false }

        do {
            var params: [String: any Sendable] = [
                "doc_id": docId,
                "generate_summary": generateSummary,
                "generate_tags": generateTags,
            ]
            if let path = projectPath {
                params["project_path"] = path
            }

            let response: AutoEnhanceDocResponse = try await bridge.call("docs.auto_enhance_doc", params: params)

            if response.success, let doc = response.doc {
                let enhancements = response.enhancements ?? []
                if !enhancements.isEmpty {
                    notifications.add(.success("Enhanced document with \(enhancements.joined(separator: ", "))"))
                }
                return doc
            } else if let error = response.error {
                lastError = error
                notifications.add(.error("Auto-enhance failed: \(error)"))
            }
        } catch {
            lastError = error.localizedDescription
            notifications.add(.error("Auto-enhance failed: \(error.localizedDescription)"))
        }
        return nil
    }

    // MARK: - Language Detection

    func detectLanguage(_ code: String) async -> String? {
        do {
            let params: [String: any Sendable] = ["code": code]
            let response: DetectLanguageResponse = try await bridge.call("ai.detect_language", params: params)

            if response.success, let language = response.language {
                return language
            }
        } catch {
            // Silent fail
        }
        return nil
    }

    // MARK: - Translation

    func translate(_ text: String, sourceLang: String, targetLang: String) async -> String? {
        isProcessing = true
        defer { isProcessing = false }

        do {
            let params: [String: any Sendable] = [
                "text": text,
                "source_lang": sourceLang,
                "target_lang": targetLang,
            ]

            let response: TranslateResponse = try await bridge.call("ai.translate", params: params)

            if response.success, let translated = response.translated {
                return translated
            } else if let error = response.error {
                lastError = error
            }
        } catch {
            lastError = error.localizedDescription
        }
        return nil
    }
}
