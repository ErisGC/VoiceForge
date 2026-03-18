// Models for subscription and usage data.

/// Summary of a user's current plan and resource usage.
class UsageSummary {
  final String plan;
  final String status;
  final int conversionsUsed;
  final int conversionsLimit;
  final int conversionsRemaining;
  final int profilesUsed;
  final int profilesLimit;
  final String period;

  const UsageSummary({
    required this.plan,
    required this.status,
    required this.conversionsUsed,
    required this.conversionsLimit,
    required this.conversionsRemaining,
    required this.profilesUsed,
    required this.profilesLimit,
    required this.period,
  });

  factory UsageSummary.fromJson(Map<String, dynamic> json) {
    return UsageSummary(
      plan: json['plan'] as String? ?? 'free',
      status: json['status'] as String? ?? 'active',
      conversionsUsed: json['conversions_used'] as int? ?? 0,
      conversionsLimit: json['conversions_limit'] as int? ?? 3,
      conversionsRemaining: json['conversions_remaining'] as int? ?? 0,
      profilesUsed: json['profiles_used'] as int? ?? 0,
      profilesLimit: json['profiles_limit'] as int? ?? 1,
      period: json['period'] as String? ?? '',
    );
  }

  bool get isFree => plan == 'free';
  bool get isPro => plan == 'pro';
  bool get isUnlimited => plan == 'unlimited';
  bool get hasWatermark => isFree;
  bool get isConversionQuotaExceeded =>
      conversionsLimit != -1 && conversionsUsed >= conversionsLimit;
  bool get isProfileQuotaExceeded =>
      profilesLimit != -1 && profilesUsed >= profilesLimit;

  String get planDisplayName {
    switch (plan) {
      case 'pro':
        return 'Pro';
      case 'unlimited':
        return 'Unlimited';
      default:
        return 'Gratis';
    }
  }

  String get conversionsDisplay {
    if (conversionsLimit == -1) return 'Ilimitadas';
    return '$conversionsUsed / $conversionsLimit';
  }

  String get profilesDisplay {
    if (profilesLimit == -1) return 'Ilimitados';
    return '$profilesUsed / $profilesLimit';
  }

  double get conversionProgress {
    if (conversionsLimit <= 0) return 0.0;
    return (conversionsUsed / conversionsLimit).clamp(0.0, 1.0);
  }
}

class QuotaCheck {
  final bool allowed;
  final String plan;
  final int used;
  final int limit;
  final String upgradeUrl;

  const QuotaCheck({
    required this.allowed,
    required this.plan,
    required this.used,
    required this.limit,
    this.upgradeUrl = 'https://voiceforge.app/#precio',
  });

  factory QuotaCheck.fromJson(Map<String, dynamic> json) {
    return QuotaCheck(
      allowed: json['allowed'] as bool? ?? false,
      plan: json['plan'] as String? ?? 'free',
      used: json['used'] as int? ?? 0,
      limit: json['limit'] as int? ?? 0,
      upgradeUrl: json['upgrade_url'] as String? ?? 'https://voiceforge.app/#precio',
    );
  }
}
