# -*- coding: utf-8 -*-
import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Wrote {path}")

# 1. zeepub_queue_item.dart
write_file(r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\data\models\zeepub_queue_item.dart", """class ZeepubQueueItem {
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

  String get bookTitle => seriesSpanish?.isNotEmpty == true
      ? seriesSpanish!
      : (seriesEnglish?.isNotEmpty == true ? seriesEnglish! : (series?.isNotEmpty == true ? series! : 'Tomo $bookHash'));
  String get channelName => channel?.isNotEmpty == true ? channel! : (channelId != null ? 'Canal $channelId' : 'Canal Oficial');
  String get scheduledAt => scheduledFor ?? '';
  String? get errorMessage => error;
}
""")

# 2. zeepub_post_item.dart
write_file(r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\data\models\zeepub_post_item.dart", """class ZeepubPostItem {
  final String id;
  final String bookHash;
  final String? title;
  final String? series;
  final double? volume;
  final String? channel;
  final String platform;
  final String publishedAt;
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
    this.publishedAt = '',
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

  String get bookTitle => title?.isNotEmpty == true ? title! : (series?.isNotEmpty == true ? series! : 'Tomo $bookHash');
  String get channelName => channel?.isNotEmpty == true ? channel! : 'Canal Oficial';
  String get channelId => channel?.isNotEmpty == true ? channel! : '1';
  String? get messageId => id.isNotEmpty ? id : null;
}
""")

# 3. inject_dependencies.dart
write_file(r"E:\Descargas\ZeeTools\lib\inject_dependencies.dart", """import 'package:flutter/foundation.dart';
import 'package:get_it/get_it.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'common/epub/repositories/epub_repo.dart';
import 'common/process/native_tools_repo.dart';
import 'common/widgets/speed_dial.dart';
import 'features/epub_migrator/data/epub_migrator_repo.dart';
import 'features/epub_migrator/presentation/cubit/epub_migrator_cubit.dart';
import 'features/epub_templater/data/amazon_repo.dart';
import 'features/epub_templater/data/epub_templater_repo.dart';
import 'features/epub_templater/data/template_profiles_repo.dart';
import 'features/epub_templater/presentation/cubit/epub_templater_cubit.dart';
import 'features/home/data/layout_repo.dart';
import 'features/image_optimizer/data/image_optimizer_engine.dart';
import 'features/image_optimizer/data/image_optimizer_repo.dart';
import 'features/image_optimizer/data/image_optimizer_settings_repo.dart';
import 'features/image_optimizer/presentation/cubit/image_optimizer_cubit.dart';
import 'features/metadata_editor/data/epub_metadata_repo.dart';
import 'features/metadata_editor/presentation/cubit/metadata_editor_cubit.dart';
import 'features/search_replace/data/search_replace_repo.dart';
import 'features/search_replace/data/search_replace_settings_repo.dart';
import 'features/search_replace/presentation/cubit/search_replace_cubit.dart';
import 'features/settings/data/preferences_repo.dart';
import 'features/settings/presentation/cubit/settings_cubit.dart';
import 'features/zeepub_editorial/data/datasources/zeepub_api_client.dart';
import 'features/zeepub_editorial/data/repositories/zeepub_editorial_repository.dart';
import 'features/zeepub_editorial/presentation/cubit/zeepub_editorial_cubit.dart';

final getIt = GetIt.instance;

Future<void> injectDependencies() async {
  // Externals
  final prefs = await SharedPreferences.getInstance();
  getIt.registerLazySingleton<SharedPreferences>(() => prefs);
  final supportDir = await getApplicationSupportDirectory();

  // Repositories
  getIt.registerLazySingleton<EpubRepository>(() => EpubRepositoryImpl());
  getIt.registerLazySingleton<SearchReplaceRepository>(() => SearchReplaceRepositoryImpl(getIt()));
  getIt.registerLazySingleton<PreferencesRepository>(() => PreferencesRepositoryImpl(getIt()));
  getIt.registerLazySingleton<LayoutRepository>(() => LayoutRepositoryImpl(getIt()));
  getIt.registerLazySingleton<SearchReplaceSettingsRepository>(() => SearchReplaceSettingsRepositoryImpl(getIt()));
  getIt.registerLazySingleton<NativeToolsRepository>(() => NativeToolsRepositoryImpl(p.join(supportDir.path, 'tools')));
  getIt.registerLazySingleton<ImageOptimizerSettingsRepository>(() => ImageOptimizerSettingsRepositoryImpl(getIt()));
  getIt.registerLazySingleton<ImageOptimizerRepository>(() => ImageOptimizerRepositoryImpl(EpubRepositoryImpl(), getIt(), ImageOptimizerEngine()));
  getIt.registerLazySingleton<EpubTemplaterRepository>(() => EpubTemplaterRepositoryImpl());
  getIt.registerLazySingleton<TemplateProfilesRepository>(() => TemplateProfilesRepositoryImpl(getIt(), p.join(supportDir.path, 'perfiles')));
  getIt.registerLazySingleton<AmazonRepository>(() => AmazonRepositoryImpl(p.join(supportDir.path, 'amazon')));
  getIt.registerLazySingleton<EpubMigratorRepository>(() => EpubMigratorRepositoryImpl());
  getIt.registerLazySingleton<EpubMetadataRepository>(() => EpubMetadataRepositoryImpl(EpubRepositoryImpl()));

  // ZeePub Editorial
  getIt.registerLazySingleton<ZeepubApiClient>(() => ZeepubApiClient());
  getIt.registerLazySingleton<ZeepubEditorialRepository>(() => ZeepubEditorialRepository(client: getIt()));

  // Cubits
  getIt.registerFactory<SearchReplaceCubit>(() => SearchReplaceCubit(getIt(), getIt(), getIt()));
  getIt.registerFactory<SettingsCubit>(() => SettingsCubit(getIt()));
  getIt.registerFactory<ImageOptimizerCubit>(() => ImageOptimizerCubit(getIt(), getIt()));
  getIt.registerFactory<EpubTemplaterCubit>(() => EpubTemplaterCubit(getIt(), getIt(), getIt(), getIt()));
  getIt.registerFactory<MetadataEditorCubit>(() => MetadataEditorCubit(getIt()));
  getIt.registerFactory<EpubMigratorCubit>(() => EpubMigratorCubit(getIt()));
  getIt.registerFactory<ZeepubEditorialCubit>(() => ZeepubEditorialCubit(repository: getIt()));

  getIt.registerLazySingleton<ValueNotifier<List<SpeedDialAction>>>(() => ValueNotifier<List<SpeedDialAction>>([]));
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
      final seriesRes = await _repo.getSeriesList();
      final channels = await _repo.getChannels();
      final templates = await _repo.getTemplates();
      final queue = await _repo.getQueue();
      final posts = await _repo.getPostsHistory();

      emit(state.copyWith(
        workgroups: workgroups,
        seriesList: seriesRes.items,
        totalSeries: seriesRes.total,
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
      final res = await _repo.getSeriesList(query: query);
      emit(state.copyWith(seriesList: res.items, totalSeries: res.total));
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

# 5. series_list_widget.dart fix saveSeries return
s_path = r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\views\widgets\series_list_widget.dart"
with open(s_path, 'r', encoding='utf-8') as f:
    s_content = f.read()

s_content = s_content.replace(
    'final ok = await context.read<ZeepubEditorialCubit>().saveSeries(series.seriesHash, payload);\n              if (ok && ctx.mounted) {',
    'await context.read<ZeepubEditorialCubit>().saveSeries(series.seriesHash, payload);\n              if (ctx.mounted) {'
)
with open(s_path, 'w', encoding='utf-8') as f:
    f.write(s_content)
print("Updated series_list_widget.dart")

# 6. zeepub_editorial_view.dart fix SeriesListWidget(baseUrl: state.baseUrl)
e_path = r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\views\zeepub_editorial_view.dart"
with open(e_path, 'r', encoding='utf-8') as f:
    e_content = f.read()

e_content = e_content.replace('const SeriesListWidget(),', 'SeriesListWidget(baseUrl: state.baseUrl),')
with open(e_path, 'w', encoding='utf-8') as f:
    f.write(e_content)
print("Updated zeepub_editorial_view.dart")

# 7. zeepub_volume_edit_view.dart remove unused import
v_path = r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\views\zeepub_volume_edit_view.dart"
with open(v_path, 'r', encoding='utf-8') as f:
    v_content = f.read()

v_content = v_content.replace("import 'widgets/telegram_publish_dialog.dart';\n", "")
with open(v_path, 'w', encoding='utf-8') as f:
    f.write(v_content)
print("Updated zeepub_volume_edit_view.dart")
