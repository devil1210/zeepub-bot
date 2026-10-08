# -*- coding: utf-8 -*-
import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Wrote {path}")

# 1. zeepub_post_item.dart
write_file(r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\data\models\zeepub_post_item.dart", """class ZeepubPostItem {
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
      publishedAt: json['published_at']?.toString() ?? '',
      postUrl: json['post_url']?.toString(),
      coverUrl: json['cover_url']?.toString(),
      caption: json['caption']?.toString(),
    );
  }

  String get bookTitle => title ?? '';
  String get channelName => channel ?? '';
  String? get messageId => id.isNotEmpty ? id : null;
}
""")

# 2. zeepub_channel.dart
write_file(r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\data\models\zeepub_channel.dart", """class ZeepubChannel {
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

  bool get isDefault => isFavorite;
  String get channelId => targetId;
}
""")

# 3. zeepub_ai_suggestion.dart
write_file(r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\data\models\zeepub_ai_suggestion.dart", """class ZeepubAiSuggestion {
  final String spanishTitle;
  final String englishTitle;
  final String author;
  final double? volume;
  final String demography;

  const ZeepubAiSuggestion({
    this.spanishTitle = '',
    this.englishTitle = '',
    this.author = '',
    this.volume,
    this.demography = '',
  });

  factory ZeepubAiSuggestion.fromJson(Map<String, dynamic> json) {
    return ZeepubAiSuggestion(
      spanishTitle: (json['spanish_title'] ?? json['series_spanish'] ?? '').toString(),
      englishTitle: (json['english_title'] ?? json['series_english'] ?? '').toString(),
      author: (json['author'] ?? '').toString(),
      volume: json['volume'] != null ? (json['volume'] as num).toDouble() : null,
      demography: (json['demography'] ?? '').toString(),
    );
  }

  String get seriesSpanish => spanishTitle;
  String get illustrator => '';
  String get publisher => '';
}
""")

# 4. zeepub_editorial_cubit.dart
write_file(r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\cubit\zeepub_editorial_cubit.dart", """import 'package:flutter_bloc/flutter_bloc.dart';

import '/features/zeepub_editorial/data/models/zeepub_volume.dart';
import '/features/zeepub_editorial/data/repositories/zeepub_editorial_repository.dart';
import 'zeepub_editorial_state.dart';

class ZeepubEditorialCubit extends Cubit<ZeepubEditorialState> {
  final ZeepubEditorialRepository _repo;

  ZeepubEditorialCubit({ZeepubEditorialRepository? repository})
      : _repo = repository ?? ZeepubEditorialRepository(),
        super(const ZeepubEditorialState());

  Future<void> init() async {
    emit(state.copyWith(loading: true, clearError: true));
    try {
      final workgroups = await _repo.getWorkgroups();
      final series = await _repo.getSeriesList();
      final channels = await _repo.getChannels();
      final templates = await _repo.getTemplates();
      final queue = await _repo.getQueue();
      final posts = await _repo.getPostsHistory();

      emit(state.copyWith(
        workgroups: workgroups,
        seriesList: series,
        totalSeries: series.length,
        channels: channels,
        templates: templates,
        queue: queue,
        posts: posts,
        baseUrl: _repo.baseUrl,
      ));

      await loadVolumes(page: 1);
    } catch (e) {
      emit(state.copyWith(
        loading: false,
        errorMessage: 'Error al conectar con la API de ZeePub: $e',
      ));
    }
  }

  Future<void> setBaseUrl(String url) async {
    await _repo.saveBaseUrl(url);
    emit(state.copyWith(baseUrl: url));
    await init();
  }

  // --- Volumes ---

  Future<void> loadVolumes({
    int page = 1,
    String? query,
    String? seriesId,
    int? workgroupId,
    String? colorMode,
    bool? uncensored,
  }) async {
    emit(state.copyWith(loading: true, clearError: true));
    try {
      final res = await _repo.getVolumes(
        page: page,
        query: query ?? state.searchQuery,
        seriesId: seriesId ?? state.selectedSeriesId,
        workgroupId: workgroupId ?? state.selectedWorkgroupId,
        colorMode: colorMode ?? state.selectedColorMode,
        isUncensored: uncensored ?? state.filterUncensored,
      );

      emit(state.copyWith(
        loading: false,
        volumes: res.items,
        totalVolumes: res.total,
        currentPage: res.page,
        totalPages: res.totalPages,
        searchQuery: query ?? state.searchQuery,
        selectedSeriesId: seriesId ?? state.selectedSeriesId,
        selectedWorkgroupId: workgroupId ?? state.selectedWorkgroupId,
        selectedColorMode: colorMode ?? state.selectedColorMode,
        filterUncensored: uncensored ?? state.filterUncensored,
      ));
    } catch (e) {
      emit(state.copyWith(loading: false, errorMessage: 'Error al cargar tomos: $e'));
    }
  }

  void openVolumeDetail(ZeepubVolume volume) {
    emit(state.copyWith(activeVolume: volume, clearAiSuggestion: true));
  }

  void closeVolumeDetail() {
    emit(state.copyWith(clearActiveVolume: true, clearAiSuggestion: true));
  }

  void openPublisher(ZeepubVolume volume) {
    emit(state.copyWith(publishingVolume: volume));
  }

  void closePublisher() {
    emit(state.copyWith(clearPublishingVolume: true));
  }

  Future<void> saveVolume(String bookHash, Map<String, dynamic> payload) async {
    emit(state.copyWith(saving: true, clearError: true));
    try {
      await _repo.updateVolume(bookHash, payload);
      final updatedVol = await _repo.getVolumeDetail(bookHash);
      emit(state.copyWith(
        saving: false,
        activeVolume: updatedVol,
        successMessage: 'Metadatos guardados correctamente',
      ));
      await loadVolumes(page: state.currentPage);
    } catch (e) {
      emit(state.copyWith(saving: false, errorMessage: 'Error al guardar: $e'));
    }
  }

  Future<void> syncVolumeFromDisk(String bookHash) async {
    emit(state.copyWith(saving: true, clearError: true));
    try {
      await _repo.syncVolumeFile(bookHash);
      final updatedVol = await _repo.getVolumeDetail(bookHash);
      emit(state.copyWith(
        saving: false,
        activeVolume: updatedVol,
        successMessage: 'Archivo re-escaneado desde disco correctamente',
      ));
      await loadVolumes(page: state.currentPage);
    } catch (e) {
      emit(state.copyWith(saving: false, errorMessage: 'Error al re-escanear: $e'));
    }
  }

  // --- Series ---

  Future<void> loadSeries({String? query}) async {
    try {
      final list = await _repo.getSeriesList(query: query);
      emit(state.copyWith(seriesList: list, totalSeries: list.length));
    } catch (e) {
      emit(state.copyWith(errorMessage: 'Error al cargar series: $e'));
    }
  }

  Future<void> saveSeries(String seriesHash, Map<String, dynamic> payload) async {
    emit(state.copyWith(saving: true, clearError: true));
    try {
      await _repo.updateSeries(seriesHash, payload);
      emit(state.copyWith(saving: false, successMessage: 'Serie actualizada correctamente'));
      await loadSeries();
    } catch (e) {
      emit(state.copyWith(saving: false, errorMessage: 'Error al guardar serie: $e'));
    }
  }

  // --- AI ---

  Future<void> requestAiSuggestion(String title) async {
    emit(state.copyWith(aiLoading: true, clearError: true));
    try {
      final suggestion = await _repo.aiSuggestMetadata(title);
      emit(state.copyWith(
        aiLoading: false,
        latestAiSuggestion: suggestion,
        successMessage: suggestion != null ? 'Sugerencias de IA listas' : null,
      ));
    } catch (e) {
      emit(state.copyWith(aiLoading: false, errorMessage: 'Error al invocar IA: $e'));
    }
  }

  // --- Channels ---

  Future<void> loadChannels() async {
    try {
      final channels = await _repo.getChannels();
      emit(state.copyWith(channels: channels));
    } catch (e) {
      emit(state.copyWith(errorMessage: 'Error al cargar canales: $e'));
    }
  }

  Future<void> saveChannel(Map<String, dynamic> payload) async {
    emit(state.copyWith(saving: true, clearError: true));
    try {
      await _repo.saveChannel(payload);
      emit(state.copyWith(saving: false, successMessage: 'Canal guardado correctamente'));
      await loadChannels();
    } catch (e) {
      emit(state.copyWith(saving: false, errorMessage: 'Error al guardar canal: $e'));
    }
  }

  Future<void> deleteChannel(int channelId) async {
    try {
      await _repo.deleteChannel(channelId);
      emit(state.copyWith(successMessage: 'Canal eliminado'));
      await loadChannels();
    } catch (e) {
      emit(state.copyWith(errorMessage: 'Error al eliminar canal: $e'));
    }
  }

  // --- Templates ---

  Future<void> loadTemplates() async {
    try {
      final templates = await _repo.getTemplates();
      emit(state.copyWith(templates: templates));
    } catch (e) {
      emit(state.copyWith(errorMessage: 'Error al cargar plantillas: $e'));
    }
  }

  Future<void> saveTemplate(Map<String, dynamic> payload) async {
    emit(state.copyWith(saving: true, clearError: true));
    try {
      await _repo.saveTemplate(payload);
      emit(state.copyWith(saving: false, successMessage: 'Plantilla guardada correctamente'));
      await loadTemplates();
    } catch (e) {
      emit(state.copyWith(saving: false, errorMessage: 'Error al guardar plantilla: $e'));
    }
  }

  Future<void> deleteTemplate(int templateId) async {
    try {
      await _repo.deleteTemplate(templateId);
      emit(state.copyWith(successMessage: 'Plantilla eliminada'));
      await loadTemplates();
    } catch (e) {
      emit(state.copyWith(errorMessage: 'Error al eliminar plantilla: $e'));
    }
  }

  Future<void> restoreTemplates() async {
    emit(state.copyWith(saving: true, clearError: true));
    try {
      await _repo.restoreTemplates();
      emit(state.copyWith(saving: false, successMessage: 'Plantillas oficiales restauradas'));
      await loadTemplates();
    } catch (e) {
      emit(state.copyWith(saving: false, errorMessage: 'Error al restaurar: $e'));
    }
  }

  // --- Queue / Calendar ---

  Future<void> loadQueue() async {
    try {
      final queue = await _repo.getQueue();
      emit(state.copyWith(queue: queue));
    } catch (e) {
      emit(state.copyWith(errorMessage: 'Error al cargar agenda: $e'));
    }
  }

  Future<void> cancelQueueItem(int id) async {
    try {
      await _repo.cancelQueueItem(id);
      emit(state.copyWith(successMessage: 'Publicación cancelada'));
      await loadQueue();
    } catch (e) {
      emit(state.copyWith(errorMessage: 'Error al cancelar: $e'));
    }
  }

  Future<void> retryQueueItem(int id) async {
    try {
      await _repo.retryQueueItem(id);
      emit(state.copyWith(successMessage: 'Publicación reintentada'));
      await loadQueue();
    } catch (e) {
      emit(state.copyWith(errorMessage: 'Error al reintentar: $e'));
    }
  }

  // --- Posts ---

  Future<void> loadPosts() async {
    try {
      final posts = await _repo.getPostsHistory();
      emit(state.copyWith(posts: posts));
    } catch (e) {
      emit(state.copyWith(errorMessage: 'Error al cargar historial: $e'));
    }
  }

  // --- Publication ---

  Future<void> publishNow({
    required String bookHash,
    int? channelId,
    int? templateId,
    String? customCaption,
    bool sendAsFile = true,
  }) async {
    emit(state.copyWith(saving: true, clearError: true));
    try {
      await _repo.publishNow(
        bookHash: bookHash,
        channelId: channelId,
        templateId: templateId,
        customCaption: customCaption,
        sendAsFile: sendAsFile,
      );
      emit(state.copyWith(
        saving: false,
        clearPublishingVolume: true,
        successMessage: '¡Publicación enviada inmediatamente al canal!',
      ));
      await loadPosts();
    } catch (e) {
      emit(state.copyWith(saving: false, errorMessage: 'Error al publicar: $e'));
    }
  }

  Future<void> schedulePublication({
    required String bookHash,
    required String scheduledAtIso,
    int? channelId,
    int? templateId,
    String? customCaption,
    bool sendAsFile = true,
  }) async {
    emit(state.copyWith(saving: true, clearError: true));
    try {
      await _repo.schedulePublication(
        bookHash: bookHash,
        scheduledAtIso: scheduledAtIso,
        channelId: channelId,
        templateId: templateId,
        customCaption: customCaption,
        sendAsFile: sendAsFile,
      );
      emit(state.copyWith(
        saving: false,
        clearPublishingVolume: true,
        successMessage: 'Publicación agendada con éxito',
      ));
      await loadQueue();
    } catch (e) {
      emit(state.copyWith(saving: false, errorMessage: 'Error al agendar: $e'));
    }
  }

  void clearNotifications() {
    emit(state.copyWith(clearError: true, clearSuccess: true));
  }
}
""")

# 5. telegram_publish_dialog.dart
write_file(r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\views\widgets\telegram_publish_dialog.dart", """import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '/features/zeepub_editorial/data/models/zeepub_volume.dart';
import '/features/zeepub_editorial/presentation/cubit/zeepub_editorial_cubit.dart';
import '/features/zeepub_editorial/presentation/cubit/zeepub_editorial_state.dart';

class TelegramPublishDialog extends StatefulWidget {
  final ZeepubVolume volume;
  final String baseUrl;

  const TelegramPublishDialog({
    super.key,
    required this.volume,
    required this.baseUrl,
  });

  @override
  State<TelegramPublishDialog> createState() => _TelegramPublishDialogState();
}

class _TelegramPublishDialogState extends State<TelegramPublishDialog> {
  bool _isScheduled = false;
  DateTime _scheduledDateTime = DateTime.now().add(const Duration(hours: 1));
  final TextEditingController _captionController = TextEditingController();
  final bool _sendAsFile = true;

  @override
  void dispose() {
    _captionController.dispose();
    super.dispose();
  }

  Future<void> _pickDateTime() async {
    final date = await showDatePicker(
      context: context,
      initialDate: _scheduledDateTime,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (date == null || !mounted) return;

    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(_scheduledDateTime),
    );
    if (time == null || !mounted) return;

    setState(() {
      _scheduledDateTime = DateTime(date.year, date.month, date.day, time.hour, time.minute);
    });
  }

  Future<void> _handleSubmit() async {
    final cubit = context.read<ZeepubEditorialCubit>();
    final customCaption = _captionController.text.trim().isNotEmpty ? _captionController.text.trim() : null;

    if (_isScheduled) {
      await cubit.schedulePublication(
        bookHash: widget.volume.bookHash,
        scheduledAtIso: _scheduledDateTime.toIso8601String(),
        customCaption: customCaption,
        sendAsFile: _sendAsFile,
      );
    } else {
      await cubit.publishNow(
        bookHash: widget.volume.bookHash,
        customCaption: customCaption,
        sendAsFile: _sendAsFile,
      );
    }

    if (mounted) {
      Navigator.of(context).pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final tt = Theme.of(context).textTheme;

    return BlocBuilder<ZeepubEditorialCubit, ZeepubEditorialState>(
      builder: (BuildContext context, ZeepubEditorialState state) {
        return Dialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 580),
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    children: [
                      Icon(Icons.send_rounded, color: cs.primary, size: 28),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          'Publicar en Canal de Telegram',
                          style: tt.titleLarge?.copyWith(fontWeight: FontWeight.bold),
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close),
                        onPressed: () => Navigator.of(context).pop(),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  const Divider(),
                  const SizedBox(height: 12),

                  // Book Summary Card
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: cs.surfaceContainerHighest.withValues(alpha: 0.5),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          widget.volume.spanishTitle.isNotEmpty
                              ? widget.volume.spanishTitle
                              : widget.volume.title,
                          style: tt.titleSmall?.copyWith(fontWeight: FontWeight.bold),
                        ),
                        if (widget.volume.volume != null)
                          Text('Volumen ${widget.volume.volume}', style: tt.bodySmall),
                        Text(
                          'Fansub: ${widget.volume.publisher ?? "Sin fansub"} | Trad: ${widget.volume.translator ?? "N/A"}',
                          style: tt.labelSmall?.copyWith(color: cs.onSurfaceVariant),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 16),

                  // Mode Selector
                  SegmentedButton<bool>(
                    segments: const [
                      ButtonSegment(
                        value: false,
                        label: Text('Publicar Ahora'),
                        icon: Icon(Icons.send_rounded),
                      ),
                      ButtonSegment(
                        value: true,
                        label: Text('Programar'),
                        icon: Icon(Icons.schedule_rounded),
                      ),
                    ],
                    selected: {_isScheduled},
                    onSelectionChanged: (set) {
                      setState(() {
                        _isScheduled = set.first;
                      });
                    },
                  ),

                  if (_isScheduled) ...[
                    const SizedBox(height: 16),
                    ListTile(
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                        side: BorderSide(color: cs.outlineVariant),
                      ),
                      leading: Icon(Icons.calendar_today_rounded, color: cs.primary),
                      title: const Text('Fecha y Hora programada'),
                      subtitle: Text(_scheduledDateTime.toString().substring(0, 16)),
                      trailing: TextButton(
                        onPressed: _pickDateTime,
                        child: const Text('Cambiar'),
                      ),
                    ),
                  ],

                  const SizedBox(height: 16),

                  TextField(
                    controller: _captionController,
                    maxLines: 2,
                    decoration: const InputDecoration(
                      labelText: 'Mensaje / Caption personalizado (Opcional)',
                      hintText: 'Dejar vacío para usar la plantilla automática estándar...',
                    ),
                  ),

                  const SizedBox(height: 24),

                  Row(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      TextButton(
                        onPressed: state.saving ? null : () => Navigator.of(context).pop(),
                        child: const Text('Cancelar'),
                      ),
                      const SizedBox(width: 12),
                      FilledButton.icon(
                        icon: state.saving
                            ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                            : Icon(_isScheduled ? Icons.schedule_send : Icons.send_rounded, size: 18),
                        label: Text(_isScheduled ? 'Programar Envío' : 'Publicar Inmediatamente'),
                        onPressed: state.saving ? null : _handleSubmit,
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}
""")

print("Patched all models, cubit, and dialog!")
