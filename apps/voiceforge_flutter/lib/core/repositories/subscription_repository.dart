import '../models/subscription_models.dart';
import '../network/api_client.dart';

/// Repository for subscription and usage quota API calls.
///
/// Results are cached for [_cacheDuration] to avoid hammering the
/// server on every navigation.
class SubscriptionRepository {
  SubscriptionRepository({required ApiClient apiClient})
      : _apiClient = apiClient;

  final ApiClient _apiClient;

  static const _cacheDuration = Duration(minutes: 5);
  UsageSummary? _cachedSummary;
  DateTime? _cacheTimestamp;

  /// Fetch usage summary (cached for 5 minutes).
  Future<UsageSummary> getUsageSummary({bool forceRefresh = false}) async {
    if (!forceRefresh && _cachedSummary != null && _cacheTimestamp != null) {
      final elapsed = DateTime.now().difference(_cacheTimestamp!);
      if (elapsed < _cacheDuration) {
        return _cachedSummary!;
      }
    }

    final data = await _apiClient.getJson('/api/v1/subscriptions/usage');
    final summary = UsageSummary.fromJson(data as Map<String, dynamic>);
    _cachedSummary = summary;
    _cacheTimestamp = DateTime.now();
    return summary;
  }

  /// Quick check: can the user convert?
  Future<QuotaCheck> canConvert() async {
    final data = await _apiClient.getJson('/api/v1/subscriptions/can-convert');
    return QuotaCheck.fromJson(data as Map<String, dynamic>);
  }

  /// Quick check: can the user create another profile?
  Future<QuotaCheck> canCreateProfile() async {
    final data =
        await _apiClient.getJson('/api/v1/subscriptions/can-create-profile');
    return QuotaCheck.fromJson(data as Map<String, dynamic>);
  }

  /// Cancel the active subscription.
  Future<void> cancelSubscription() async {
    await _apiClient.postJson(
      '/api/v1/subscriptions/cancel',
      body: {},
    );
    invalidateCache();
  }

  /// Clear the cached summary (call after actions that change usage).
  void invalidateCache() {
    _cachedSummary = null;
    _cacheTimestamp = null;
  }
}
