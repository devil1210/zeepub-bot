# -*- coding: utf-8 -*-
import os

base_dir = r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial"
models_dir = os.path.join(base_dir, "data", "models")
datasources_dir = os.path.join(base_dir, "data", "datasources")
repositories_dir = os.path.join(base_dir, "data", "repositories")
cubit_dir = os.path.join(base_dir, "presentation", "cubit")
views_dir = os.path.join(base_dir, "presentation", "views")
widgets_dir = os.path.join(views_dir, "widgets")

os.makedirs(models_dir, exist_ok=True)
os.makedirs(widgets_dir, exist_ok=True)

# 1. Models
channel_model = r'''class ZeepubChannel {
  final int id;
  final String name;
  final String platform;
  final String targetId;
  final bool isActive;
  final bool isFavorite;
  final String? type;
  final int? subscribersCount;

  const ZeepubChannel({
    required this.id,
    required this.name,
    this.platform = 'telegram',
    required this.targetId,
    this.isActive = true,
    this.isFavorite = false,
    this.type,
    this.subscribersCount,
  });

  factory ZeepubChannel.fromJson(Map<String, dynamic> json) {
    return ZeepubChannel(
      id: (json['id'] as num?)?.toInt() ?? 0,
      name: (json['name'] ?? '').toString(),
      platform: (json['platform'] ?? 'telegram').toString(),
      targetId: (json['target_id'] ?? json['targetId'] ?? '').toString(),
      isActive: json['is_active'] ?? json['isActive'] ?? true,
      isFavorite: json['is_favorite'] ?? json['isFavorite'] ?? false,
      type: json['type']?.toString(),
      subscribersCount: (json['subscribers_count'] ?? json['subscribersCount']) != null
          ? (json['subscribers_count'] ?? json['subscribersCount'] as num).toInt()
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'platform': platform,
      'target_id': targetId,
      'is_active': isActive,
      'is_favorite': isFavorite,
      'type': type,
    };
  }
}
'''

template_model = r'''class ZeepubTemplate {
  final int? id;
  final String name;
  final String content;
  final String platform;
  final bool isDefault;
  final Map<String, dynamic>? extraConfig;

  const ZeepubTemplate({
    this.id,
    required this.name,
    required this.content,
    this.platform = 'telegram',
    this.isDefault = false,
    this.extraConfig,
  });

  factory ZeepubTemplate.fromJson(Map<String, dynamic> json) {
    return ZeepubTemplate(
      id: (json['id'] as num?)?.toInt(),
      name: (json['name'] ?? '').toString(),
      content: (json['content'] ?? '').toString(),
      platform: (json['platform'] ?? 'telegram').toString(),
      isDefault: json['is_default'] ?? json['isDefault'] ?? false,
      extraConfig: json['extra_config'] as Map<String, dynamic>?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      if (id != null) 'id': id,
      'name': name,
      'content': content,
      'platform': platform,
      'is_default': isDefault,
      if (extraConfig != null) 'extra_config': extraConfig,
    };
  }

  ZeepubTemplate copyWith({
    int? id,
    String? name,
    String? content,
    String? platform,
    bool? isDefault,
    Map<String, dynamic>? extraConfig,
  }) {
    return ZeepubTemplate(
      id: id ?? this.id,
      name: name ?? this.name,
      content: content ?? this.content,
      platform: platform ?? this.platform,
      isDefault: isDefault ?? this.isDefault,
      extraConfig: extraConfig ?? this.extraConfig,
    );
  }
}
'''

queue_item_model = r'''class ZeepubQueueItem {
  final int id;
  final String bookHash;
  final String? bookId;
  final String? channel;
  final int? channelId;
  final String platform;
  final String? scheduledFor;
  final String status;
  final String? publishedAt;
  final String? error;
  final String? caption;
  final String? series;
  final String? seriesSpanish;
  final String? seriesEnglish;
  final double? volume;
  final String? author;
  final String? coverUrl;

  const ZeepubQueueItem({
    required this.id,
    required this.bookHash,
    this.bookId,
    this.channel,
    this.channelId,
    this.platform = 'telegram',
    this.scheduledFor,
    this.status = 'pending',
    this.publishedAt,
    this.error,
    this.caption,
    this.series,
    this.seriesSpanish,
    this.seriesEnglish,
    this.volume,
    this.author,
    this.coverUrl,
  });

  factory ZeepubQueueItem.fromJson(Map<String, dynamic> json) {
    return ZeepubQueueItem(
      id: (json['id'] as num?)?.toInt() ?? 0,
      bookHash: (json['book_hash'] ?? json['bookId'] ?? json['book_id'] ?? '').toString(),
      bookId: json['book_id']?.toString(),
      channel: json['channel']?.toString(),
      channelId: (json['channel_id'] as num?)?.toInt(),
      platform: (json['platform'] ?? 'telegram').toString(),
      scheduledFor: json['scheduled_for']?.toString(),
      status: (json['status'] ?? 'pending').toString(),
      publishedAt: json['published_at']?.toString(),
      error: json['error']?.toString(),
      caption: json['caption']?.toString(),
      series: json['series']?.toString(),
      seriesSpanish: json['series_spanish']?.toString(),
      seriesEnglish: json['series_english']?.toString(),
      volume: (json['volume'] as num?)?.toDouble(),
      author: json['author']?.toString(),
      coverUrl: json['cover_url']?.toString(),
    );
  }
}
'''

post_item_model = r'''class ZeepubPostItem {
  final String id;
  final String bookHash;
  final String? title;
  final String? series;
  final double? volume;
  final String? channel;
  final String platform;
  final String? publishedAt;
  final String? postUrl;
  final String? coverUrl;
  final String? caption;

  const ZeepubPostItem({
    required this.id,
    required this.bookHash,
    this.title,
    this.series,
    this.volume,
    this.channel,
    this.platform = 'telegram',
    this.publishedAt,
    this.postUrl,
    this.coverUrl,
    this.caption,
  });

  factory ZeepubPostItem.fromJson(Map<String, dynamic> json) {
    return ZeepubPostItem(
      id: (json['id'] ?? json['post_id'] ?? json['publication_id'] ?? '').toString(),
      bookHash: (json['book_hash'] ?? json['book_id'] ?? '').toString(),
      title: json['title']?.toString(),
      series: json['series']?.toString(),
      volume: (json['volume'] as num?)?.toDouble(),
      channel: json['channel']?.toString() ?? 'Canal Oficial',
      platform: (json['platform'] ?? 'telegram').toString(),
      publishedAt: json['published_at']?.toString(),
      postUrl: json['post_url']?.toString(),
      coverUrl: json['cover_url']?.toString(),
      caption: json['caption']?.toString(),
    );
  }
}
'''

with open(os.path.join(models_dir, "zeepub_channel.dart"), "w", encoding="utf-8") as f:
    f.write(channel_model)
with open(os.path.join(models_dir, "zeepub_template.dart"), "w", encoding="utf-8") as f:
    f.write(template_model)
with open(os.path.join(models_dir, "zeepub_queue_item.dart"), "w", encoding="utf-8") as f:
    f.write(queue_item_model)
with open(os.path.join(models_dir, "zeepub_post_item.dart"), "w", encoding="utf-8") as f:
    f.write(post_item_model)

print("Created Models successfully")
