# -*- coding: utf-8 -*-
import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Wrote {path}")

# =========================================================================
# 1. zeepub_api_client.dart
# =========================================================================
write_file(r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\data\datasources\zeepub_api_client.dart", '''import 'dart:convert';
import 'dart:io';

import '/features/zeepub_editorial/data/models/zeepub_ai_suggestion.dart';
import '/features/zeepub_editorial/data/models/zeepub_channel.dart';
import '/features/zeepub_editorial/data/models/zeepub_post_item.dart';
import '/features/zeepub_editorial/data/models/zeepub_queue_item.dart';
import '/features/zeepub_editorial/data/models/zeepub_series.dart';
import '/features/zeepub_editorial/data/models/zeepub_template.dart';
import '/features/zeepub_editorial/data/models/zeepub_volume.dart';
import '/features/zeepub_editorial/data/models/zeepub_workgroup.dart';

class ZeepubApiClient {
  String baseUrl;
  final HttpClient _httpClient;

  ZeepubApiClient({String? baseUrl})
      : baseUrl = baseUrl ?? 'http://localhost:8001',
        _httpClient = HttpClient()..connectionTimeout = const Duration(seconds: 15);

  void setBaseUrl(String url) {
    if (url.trim().isNotEmpty) {
      baseUrl = url.trim().replaceAll(RegExp(r"/+$"), "");
    }
  }

  Future<Map<String, dynamic>> _get(String path, [Map<String, String>? queryParams]) async {
    final uri = Uri.parse('$baseUrl$path').replace(queryParameters: queryParams);
    final request = await _httpClient.getUrl(uri);
    request.headers.set(HttpHeaders.contentTypeHeader, 'application/json');
    request.headers.set(HttpHeaders.acceptHeader, 'application/json');

    final response = await request.close();
    final responseBody = await response.transform(utf8.decoder).join();

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(responseBody) as Map<String, dynamic>;
    } else {
      throw HttpException('Error HTTP ${response.statusCode}: $responseBody', uri: uri);
    }
  }

  Future<dynamic> _getRaw(String path, [Map<String, String>? queryParams]) async {
    final uri = Uri.parse('$baseUrl$path').replace(queryParameters: queryParams);
    final request = await _httpClient.getUrl(uri);
    request.headers.set(HttpHeaders.contentTypeHeader, 'application/json');
    request.headers.set(HttpHeaders.acceptHeader, 'application/json');

    final response = await request.close();
    final responseBody = await response.transform(utf8.decoder).join();

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(responseBody);
    } else {
      throw HttpException('Error HTTP ${response.statusCode}: $responseBody', uri: uri);
    }
  }

  Future<Map<String, dynamic>> _post(String path, Map<String, dynamic> body) async {
    final uri = Uri.parse('$baseUrl$path');
    final request = await _httpClient.postUrl(uri);
    request.headers.set(HttpHeaders.contentTypeHeader, 'application/json');
    request.headers.set(HttpHeaders.acceptHeader, 'application/json');

    final jsonBytes = utf8.encode(jsonEncode(body));
    request.contentLength = jsonBytes.length;
    request.add(jsonBytes);

    final response = await request.close();
    final responseBody = await response.transform(utf8.decoder).join();

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(responseBody) as Map<String, dynamic>;
    } else {
      throw HttpException('Error HTTP ${response.statusCode}: $responseBody', uri: uri);
    }
  }

  Future<Map<String, dynamic>> _put(String path, Map<String, dynamic> body) async {
    final uri = Uri.parse('$baseUrl$path');
    final request = await _httpClient.putUrl(uri);
    request.headers.set(HttpHeaders.contentTypeHeader, 'application/json');
    request.headers.set(HttpHeaders.acceptHeader, 'application/json');

    final jsonBytes = utf8.encode(jsonEncode(body));
    request.contentLength = jsonBytes.length;
    request.add(jsonBytes);

    final response = await request.close();
    final responseBody = await response.transform(utf8.decoder).join();

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(responseBody) as Map<String, dynamic>;
    } else {
      throw HttpException('Error HTTP ${response.statusCode}: $responseBody', uri: uri);
    }
  }

  Future<Map<String, dynamic>> _delete(String path) async {
    final uri = Uri.parse('$baseUrl$path');
    final request = await _httpClient.deleteUrl(uri);
    request.headers.set(HttpHeaders.contentTypeHeader, 'application/json');
    request.headers.set(HttpHeaders.acceptHeader, 'application/json');

    final response = await request.close();
    final responseBody = await response.transform(utf8.decoder).join();

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(responseBody) as Map<String, dynamic>;
    } else {
      throw HttpException('Error HTTP ${response.statusCode}: $responseBody', uri: uri);
    }
  }

  // --- Workgroups ---
  Future<List<ZeepubWorkgroup>> getWorkgroups() async {
    final data = await _getRaw('/api/editorial/workgroups');
    if (data is List) {
      return data.map((e) => ZeepubWorkgroup.fromJson(e as Map<String, dynamic>)).toList();
    }
    return [];
  }

  // --- Volumes ---
  Future<({List<ZeepubVolume> items, int total, int page, int totalPages})> getVolumes({
    int page = 1,
    int pageSize = 30,
    String? query,
    String? seriesId,
    int? workgroupId,
    String? colorMode,
    bool? isUncensored,
  }) async {
    final params = <String, String>{
      'page': page.toString(),
      'page_size': pageSize.toString(),
    };
    if (query != null && query.isNotEmpty) params['query'] = query;
    if (seriesId != null && seriesId.isNotEmpty) params['series_id'] = seriesId;
    if (workgroupId != null) params['workgroup_id'] = workgroupId.toString();
    if (colorMode != null && colorMode.isNotEmpty) params['color_mode'] = colorMode;
    if (isUncensored != null) params['is_uncensored'] = isUncensored.toString();

    final res = await _get('/api/editorial/volumes', params);
    final itemsJson = res['items'] as List? ?? [];
    final items = itemsJson.map((e) => ZeepubVolume.fromJson(e as Map<String, dynamic>)).toList();
    final total = (res['total'] as num?)?.toInt() ?? items.length;
    final totalPages = (res['total_pages'] as num?)?.toInt() ?? 1;
    final currentPage = (res['page'] as num?)?.toInt() ?? page;

    return (items: items, total: total, page: currentPage, totalPages: totalPages);
  }

  Future<ZeepubVolume> getVolumeDetail(String bookHash) async {
    final res = await _get('/api/editorial/volumes/$bookHash');
    return ZeepubVolume.fromJson(res['item'] ?? res);
  }

  Future<void> updateVolume(String bookHash, Map<String, dynamic> payload) async {
    await _put('/api/editorial/volumes/$bookHash', payload);
  }

  Future<void> syncVolumeFile(String bookHash) async {
    await _post('/api/editorial/volumes/$bookHash/sync-file', {});
  }

  Future<Map<String, dynamic>> uploadVolumeCover(String bookHash, List<int> fileBytes, String filename) async {
    final uri = Uri.parse('$baseUrl/api/editorial/volumes/$bookHash/cover');
    final request = await _httpClient.postUrl(uri);
    final boundary = '----WebKitFormBoundary${DateTime.now().millisecondsSinceEpoch}';
    request.headers.set(HttpHeaders.contentTypeHeader, 'multipart/form-data; boundary=$boundary');

    final header = utf8.encode('--$boundary\r\nContent-Disposition: form-data; name="file"; filename="$filename"\r\nContent-Type: image/jpeg\r\n\r\n');
    final footer = utf8.encode('\r\n--$boundary--\r\n');

    request.contentLength = header.length + fileBytes.length + footer.length;
    request.add(header);
    request.add(fileBytes);
    request.add(footer);

    final response = await request.close();
    final responseBody = await response.transform(utf8.decoder).join();

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(responseBody) as Map<String, dynamic>;
    } else {
      throw HttpException('Error HTTP ${response.statusCode}: $responseBody', uri: uri);
    }
  }

  // --- Series ---
  Future<({List<ZeepubSeries> items, int total, int page})> getSeriesList({
    String? query,
    int page = 1,
    int pageSize = 50,
  }) async {
    final params = <String, String>{
      'page': page.toString(),
      'page_size': pageSize.toString(),
    };
    if (query != null && query.isNotEmpty) params['query'] = query;

    final res = await _get('/api/editorial/series', params);
    final itemsJson = res['items'] as List? ?? [];
    final items = itemsJson.map((e) => ZeepubSeries.fromJson(e as Map<String, dynamic>)).toList();
    final total = (res['total'] as num?)?.toInt() ?? items.length;
    final currentPage = (res['page'] as num?)?.toInt() ?? page;

    return (items: items, total: total, page: currentPage);
  }

  Future<void> updateSeries(String seriesHash, Map<String, dynamic> payload) async {
    await _put('/api/editorial/series/$seriesHash', payload);
  }

  // --- AI Suggestions ---
  Future<ZeepubAiSuggestion?> getAiSuggestion(String title) async {
    final res = await _get('/api/editorial/ai/suggest', {'title': title});
    if (res['suggestion'] != null) {
      return ZeepubAiSuggestion.fromJson(res['suggestion'] as Map<String, dynamic>);
    }
    return null;
  }

  // --- Channels ---
  Future<List<ZeepubChannel>> getChannels() async {
    final data = await _getRaw('/api/editorial/channels');
    if (data is List) {
      return data.map((e) => ZeepubChannel.fromJson(e as Map<String, dynamic>)).toList();
    }
    return [];
  }

  Future<void> saveChannel(Map<String, dynamic> payload) async {
    await _post('/api/editorial/channels', payload);
  }

  Future<void> deleteChannel(int channelId) async {
    await _delete('/api/editorial/channels/$channelId');
  }

  // --- Templates ---
  Future<List<ZeepubTemplate>> getTemplates() async {
    final data = await _getRaw('/api/editorial/templates');
    if (data is List) {
      return data.map((e) => ZeepubTemplate.fromJson(e as Map<String, dynamic>)).toList();
    }
    return [];
  }

  Future<void> saveTemplate(Map<String, dynamic> payload) async {
    await _post('/api/editorial/templates', payload);
  }

  Future<void> deleteTemplate(int templateId) async {
    await _delete('/api/editorial/templates/$templateId');
  }

  Future<void> restoreTemplates() async {
    await _post('/api/editorial/templates/restore', {});
  }

  // --- Queue / Calendar ---
  Future<List<ZeepubQueueItem>> getQueue() async {
    final data = await _getRaw('/api/editorial/queue');
    if (data is List) {
      return data.map((e) => ZeepubQueueItem.fromJson(e as Map<String, dynamic>)).toList();
    }
    return [];
  }

  Future<void> cancelQueueItem(int id) async {
    await _post('/api/editorial/queue/cancel', {'id': id});
  }

  Future<void> retryQueueItem(int id) async {
    await _post('/api/editorial/queue/retry', {'id': id});
  }

  // --- Posts ---
  Future<List<ZeepubPostItem>> getPostsHistory() async {
    final data = await _getRaw('/api/editorial/posts');
    if (data is List) {
      return data.map((e) => ZeepubPostItem.fromJson(e as Map<String, dynamic>)).toList();
    }
    return [];
  }

  // --- Publish ---
  Future<Map<String, dynamic>> publishNow({
    required String bookHash,
    int? channelId,
    int? templateId,
    String? customCaption,
    bool sendAsFile = true,
  }) async {
    final body = <String, dynamic>{
      'book_hash': bookHash,
      'send_as_file': sendAsFile,
    };
    if (channelId != null) body['channel_id'] = channelId;
    if (templateId != null) body['template_id'] = templateId;
    if (customCaption != null) body['custom_caption'] = customCaption;
    return await _post('/api/editorial/publish/now', body);
  }

  Future<Map<String, dynamic>> schedulePublication({
    required String bookHash,
    required String scheduledAtIso,
    int? channelId,
    int? templateId,
    String? customCaption,
    bool sendAsFile = true,
  }) async {
    final body = <String, dynamic>{
      'book_hash': bookHash,
      'scheduled_for': scheduledAtIso,
      'send_as_file': sendAsFile,
    };
    if (channelId != null) body['channel_id'] = channelId;
    if (templateId != null) body['template_id'] = templateId;
    if (customCaption != null) body['custom_caption'] = customCaption;
    return await _post('/api/editorial/publish/schedule', body);
  }
}
''')

# =========================================================================
# 2. zeepub_editorial_repository.dart
# =========================================================================
write_file(r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\data\repositories\zeepub_editorial_repository.dart", '''import '/features/zeepub_editorial/data/datasources/zeepub_api_client.dart';
import '/features/zeepub_editorial/data/models/zeepub_ai_suggestion.dart';
import '/features/zeepub_editorial/data/models/zeepub_channel.dart';
import '/features/zeepub_editorial/data/models/zeepub_post_item.dart';
import '/features/zeepub_editorial/data/models/zeepub_queue_item.dart';
import '/features/zeepub_editorial/data/models/zeepub_series.dart';
import '/features/zeepub_editorial/data/models/zeepub_template.dart';
import '/features/zeepub_editorial/data/models/zeepub_volume.dart';
import '/features/zeepub_editorial/data/models/zeepub_workgroup.dart';

class ZeepubEditorialRepository {
  final ZeepubApiClient _client;

  ZeepubEditorialRepository({ZeepubApiClient? client}) : _client = client ?? ZeepubApiClient();

  String get baseUrl => _client.baseUrl;

  Future<void> saveBaseUrl(String url) async {
    _client.setBaseUrl(url);
  }

  Future<({List<ZeepubVolume> items, int total, int page, int totalPages})> getVolumes({
    int page = 1,
    int pageSize = 30,
    String? query,
    String? seriesId,
    int? workgroupId,
    String? colorMode,
    bool? isUncensored,
  }) =>
      _client.getVolumes(
        page: page,
        pageSize: pageSize,
        query: query,
        seriesId: seriesId,
        workgroupId: workgroupId,
        colorMode: colorMode,
        isUncensored: isUncensored,
      );

  Future<ZeepubVolume> getVolumeDetail(String bookHash) => _client.getVolumeDetail(bookHash);

  Future<void> updateVolume(String bookHash, Map<String, dynamic> payload) => _client.updateVolume(bookHash, payload);

  Future<void> syncVolumeFile(String bookHash) => _client.syncVolumeFile(bookHash);

  Future<String> uploadVolumeCover(String bookHash, List<int> fileBytes, String filename) async {
    final res = await _client.uploadVolumeCover(bookHash, fileBytes, filename);
    return res['cover_url']?.toString() ?? '';
  }

  Future<({List<ZeepubSeries> items, int total, int page})> getSeriesList({
    String? query,
    int page = 1,
    int pageSize = 50,
  }) =>
      _client.getSeriesList(query: query, page: page, pageSize: pageSize);

  Future<void> updateSeries(String seriesHash, Map<String, dynamic> payload) => _client.updateSeries(seriesHash, payload);

  Future<List<ZeepubWorkgroup>> getWorkgroups() => _client.getWorkgroups();

  Future<ZeepubAiSuggestion?> aiSuggestMetadata(String title) => _client.getAiSuggestion(title);

  // Channels
  Future<List<ZeepubChannel>> getChannels() => _client.getChannels();
  Future<void> saveChannel(Map<String, dynamic> payload) => _client.saveChannel(payload);
  Future<void> deleteChannel(int channelId) => _client.deleteChannel(channelId);

  // Templates
  Future<List<ZeepubTemplate>> getTemplates() => _client.getTemplates();
  Future<void> saveTemplate(Map<String, dynamic> payload) => _client.saveTemplate(payload);
  Future<void> deleteTemplate(int templateId) => _client.deleteTemplate(templateId);
  Future<void> restoreTemplates() => _client.restoreTemplates();

  // Queue / Calendar
  Future<List<ZeepubQueueItem>> getQueue() => _client.getQueue();
  Future<void> cancelQueueItem(int id) => _client.cancelQueueItem(id);
  Future<void> retryQueueItem(int id) => _client.retryQueueItem(id);

  // Posts
  Future<List<ZeepubPostItem>> getPostsHistory() => _client.getPostsHistory();

  // Publish
  Future<Map<String, dynamic>> publishNow({
    required String bookHash,
    int? channelId,
    int? templateId,
    String? customCaption,
    bool sendAsFile = true,
  }) =>
      _client.publishNow(
        bookHash: bookHash,
        channelId: channelId,
        templateId: templateId,
        customCaption: customCaption,
        sendAsFile: sendAsFile,
      );

  Future<Map<String, dynamic>> schedulePublication({
    required String bookHash,
    required String scheduledAtIso,
    int? channelId,
    int? templateId,
    String? customCaption,
    bool sendAsFile = true,
  }) =>
      _client.schedulePublication(
        bookHash: bookHash,
        scheduledAtIso: scheduledAtIso,
        channelId: channelId,
        templateId: templateId,
        customCaption: customCaption,
        sendAsFile: sendAsFile,
      );
}
''')

# =========================================================================
# 3. zeepub_editorial_cubit.dart
# =========================================================================
write_file(r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\cubit\zeepub_editorial_cubit.dart", '''import 'package:flutter_bloc/flutter_bloc.dart';

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

  Future<String?> uploadCover(String bookHash, List<int> bytes, String filename) async {
    emit(state.copyWith(saving: true, clearError: true));
    try {
      final newCoverUrl = await _repo.uploadVolumeCover(bookHash, bytes, filename);
      final updatedVol = await _repo.getVolumeDetail(bookHash);
      emit(state.copyWith(
        saving: false,
        activeVolume: updatedVol,
        successMessage: 'Portada actualizada correctamente',
      ));
      await loadVolumes(page: state.currentPage);
      return newCoverUrl;
    } catch (e) {
      emit(state.copyWith(saving: false, errorMessage: 'Error al subir portada: $e'));
      return null;
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
''')

# =========================================================================
# 4. zeepub_volume_edit_view.dart (Clean Full Rewrite)
# =========================================================================
write_file(r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\views\zeepub_volume_edit_view.dart", '''import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '/common/theme/app_dimensions.dart';
import '/common/utils/input_formatters.dart';
import '/common/utils/uuid_v7.dart';
import '/common/widgets/app_text_field.dart';
import '/common/widgets/editable_list.dart';
import '/common/widgets/form_section.dart';
import '/common/widgets/outlined_dropdown.dart';
import '/common/widgets/responsive_row.dart';
import '/common/widgets/selection_pill.dart';
import '/common/widgets/tag_pill.dart';
import '/common/widgets/toggle_field.dart';
import '../../../epub_templater/data/epub_template_builder.dart';
import '../../../epub_templater/data/opf_metadata.dart';
import '../../../epub_templater/domain/book_metadata.dart';
import '../../../epub_templater/domain/marc_relator.dart';
import '../../../epub_templater/domain/subjects.dart';
import '../../../epub_templater/domain/title_languages.dart';
import '../../../epub_templater/presentation/views/widgets/amazon_lookup.dart';
import '../../../epub_templater/presentation/views/widgets/form_fields.dart';
import '../../data/models/zeepub_series.dart';
import '../../data/models/zeepub_volume.dart';
import '../../data/models/zeepub_workgroup.dart';
import '../cubit/zeepub_editorial_cubit.dart';
import '../cubit/zeepub_editorial_state.dart';

class ZeepubVolumeEditView extends StatefulWidget {
  final ZeepubVolume volume;
  final List<ZeepubVolume> volumes;
  final List<ZeepubSeries> seriesList;
  final List<ZeepubWorkgroup> workgroups;
  final String baseUrl;
  final VoidCallback onBack;

  const ZeepubVolumeEditView({
    super.key,
    required this.volume,
    this.volumes = const [],
    this.seriesList = const [],
    required this.workgroups,
    required this.baseUrl,
    required this.onBack,
  });

  @override
  State<ZeepubVolumeEditView> createState() => _ZeepubVolumeEditViewState();
}

class _ZeepubVolumeEditViewState extends State<ZeepubVolumeEditView> {
  double _leftPanelWidth = 300.0;
  String? _customCoverUrl;

  // Identifiers
  late String _asin;
  late String _isbn13;
  late String _isbn10;
  late String _identifier;

  // Series & Title
  OriginalLanguage? _originalLanguage;
  late bool _isStandalone;
  late String _series;
  late String _seriesSpanish;
  late String _seriesEnglish;
  late String _seriesRomaji;
  late String _seriesNative;
  late String _volumeNumber;
  late String _title;
  late String _titleSpanish;
  late String _titleEnglish;
  late String _titleRomaji;
  late String _titleNative;
  late String _titleSort;

  // People & Publication
  late List<Actor> _actors;
  late String _bookLanguage;
  late BookType _bookType;
  late String _publishDate;
  late List<String> _publishers;
  late String _colorMode;
  late bool _isUncensored;

  // Description & Classification
  late String _description;
  Demographic? _demographic;
  late Set<Subject> _selectedGenres;
  int? _rating;

  @override
  void initState() {
    super.initState();
    final v = widget.volume;

    _customCoverUrl = v.coverUrl;
    _asin = '';
    _isbn13 = '';
    _isbn10 = '';
    _identifier = v.bookHash;

    _originalLanguage = OriginalLanguage.ja;
    _isStandalone = v.volume == null && (v.seriesName == null || v.seriesName!.isEmpty);
    _series = v.seriesName ?? '';
    _seriesSpanish = v.seriesSpanish ?? '';
    _seriesEnglish = v.seriesName ?? '';
    _seriesRomaji = '';
    _seriesNative = '';
    _volumeNumber = v.volume != null ? (v.volume! % 1 == 0 ? v.volume!.toInt().toString() : v.volume!.toString()) : '';

    _title = v.title;
    _titleSpanish = v.spanishTitle;
    _titleEnglish = v.englishTitle.isNotEmpty ? v.englishTitle : v.title;
    _titleRomaji = '';
    _titleNative = '';
    _titleSort = '';

    _actors = [];
    if (v.author != null && v.author!.trim().isNotEmpty) {
      _actors.add(Actor(name: v.author!.trim(), roles: const [MarcRelator.aut], fileAs: fileAsFor(v.author!.trim())));
    }
    if (v.illustrator != null && v.illustrator!.trim().isNotEmpty) {
      _actors.add(Actor(name: v.illustrator!.trim(), roles: const [MarcRelator.ill], fileAs: fileAsFor(v.illustrator!.trim())));
    }
    if (v.translator != null && v.translator!.trim().isNotEmpty) {
      _actors.add(Actor(name: v.translator!.trim(), roles: const [MarcRelator.trl], fileAs: fileAsFor(v.translator!.trim())));
    }
    if (v.layoutBy != null && v.layoutBy!.trim().isNotEmpty) {
      _actors.add(Actor(name: v.layoutBy!.trim(), roles: const [MarcRelator.mrk], fileAs: fileAsFor(v.layoutBy!.trim())));
    }
    if (_actors.isEmpty) {
      _actors.add(const Actor(roles: [MarcRelator.aut]));
    }

    _bookLanguage = 'es';
    _bookType = BookType.ln;
    _publishDate = '';
    _publishers = [];
    if (v.publisher != null && v.publisher!.trim().isNotEmpty) {
      _publishers.add(v.publisher!.trim());
    } else {
      _publishers.add('');
    }

    _colorMode = v.colorMode ?? 'mono';
    _isUncensored = v.isUncensored;

    _description = v.description ?? '';
    _demographic = null;
    _selectedGenres = {};
    _rating = null;
  }

  void _onSeriesSelected(String selectedName) {
    final match = widget.seriesList.where((s) =>
        s.seriesEnglish.toLowerCase() == selectedName.toLowerCase() ||
        s.name.toLowerCase() == selectedName.toLowerCase() ||
        s.seriesSpanish.toLowerCase() == selectedName.toLowerCase()).firstOrNull;

    setState(() {
      _seriesEnglish = selectedName;
      _series = selectedName;
      if (match != null) {
        if (match.seriesSpanish.isNotEmpty) _seriesSpanish = match.seriesSpanish;
        if (match.author.isNotEmpty) {
          final autIdx = _actors.indexWhere((a) => a.roles.contains(MarcRelator.aut));
          if (autIdx >= 0) {
            _actors[autIdx] = _actors[autIdx].copyWith(name: match.author, fileAs: fileAsFor(match.author));
          } else {
            _actors.insert(0, Actor(name: match.author, roles: const [MarcRelator.aut], fileAs: fileAsFor(match.author)));
          }
        }
        if (match.illustrator.isNotEmpty) {
          final illIdx = _actors.indexWhere((a) => a.roles.contains(MarcRelator.ill));
          if (illIdx >= 0) {
            _actors[illIdx] = _actors[illIdx].copyWith(name: match.illustrator, fileAs: fileAsFor(match.illustrator));
          } else {
            _actors.add(Actor(name: match.illustrator, roles: const [MarcRelator.ill], fileAs: fileAsFor(match.illustrator)));
          }
        }
        if (match.publisher.isNotEmpty) {
          _publishers = [match.publisher];
        }
        if (_description.isEmpty && match.description != null && match.description!.isNotEmpty) {
          _description = descriptionFromHtml(match.description!);
        }
      }
    });
  }

  void _onTitleEnglishSelected(String selectedTitle) {
    final volMatch = widget.volumes.where((v) =>
        v.englishTitle.toLowerCase() == selectedTitle.toLowerCase() ||
        v.title.toLowerCase() == selectedTitle.toLowerCase() ||
        v.spanishTitle.toLowerCase() == selectedTitle.toLowerCase()).firstOrNull;

    final seriesMatch = widget.seriesList.where((s) =>
        s.seriesEnglish.toLowerCase() == selectedTitle.toLowerCase() ||
        s.name.toLowerCase() == selectedTitle.toLowerCase() ||
        s.seriesSpanish.toLowerCase() == selectedTitle.toLowerCase()).firstOrNull;

    setState(() {
      _titleEnglish = selectedTitle;
      _title = selectedTitle;

      if (volMatch != null) {
        if (volMatch.spanishTitle.isNotEmpty) {
          _titleSpanish = volMatch.spanishTitle;
        }
        if (_seriesEnglish.isEmpty && volMatch.seriesName != null && volMatch.seriesName!.isNotEmpty) {
          _seriesEnglish = volMatch.seriesName!;
          _series = volMatch.seriesName!;
        }
        if (_seriesSpanish.isEmpty && volMatch.seriesSpanish != null && volMatch.seriesSpanish!.isNotEmpty) {
          _seriesSpanish = volMatch.seriesSpanish!;
        }
        if (_volumeNumber.isEmpty && volMatch.volume != null) {
          _volumeNumber = volMatch.volume! % 1 == 0 ? volMatch.volume!.toInt().toString() : volMatch.volume!.toString();
        }
        if (volMatch.author != null && volMatch.author!.isNotEmpty) {
          final autIdx = _actors.indexWhere((a) => a.roles.contains(MarcRelator.aut));
          if (autIdx >= 0) {
            _actors[autIdx] = _actors[autIdx].copyWith(name: volMatch.author!, fileAs: fileAsFor(volMatch.author!));
          } else {
            _actors.insert(0, Actor(name: volMatch.author!, roles: const [MarcRelator.aut], fileAs: fileAsFor(volMatch.author!)));
          }
        }
        if (volMatch.illustrator != null && volMatch.illustrator!.isNotEmpty) {
          final illIdx = _actors.indexWhere((a) => a.roles.contains(MarcRelator.ill));
          if (illIdx >= 0) {
            _actors[illIdx] = _actors[illIdx].copyWith(name: volMatch.illustrator!, fileAs: fileAsFor(volMatch.illustrator!));
          } else {
            _actors.add(Actor(name: volMatch.illustrator!, roles: const [MarcRelator.ill], fileAs: fileAsFor(volMatch.illustrator!)));
          }
        }
        if (volMatch.publisher != null && volMatch.publisher!.isNotEmpty) {
          _publishers = [volMatch.publisher!];
        }
        if (_description.isEmpty && volMatch.description != null && volMatch.description!.isNotEmpty) {
          _description = descriptionFromHtml(volMatch.description!);
        }
      } else if (seriesMatch != null) {
        if (seriesMatch.seriesSpanish.isNotEmpty) {
          _titleSpanish = seriesMatch.seriesSpanish;
        }
        if (_seriesEnglish.isEmpty) {
          _seriesEnglish = seriesMatch.seriesEnglish.isNotEmpty ? seriesMatch.seriesEnglish : seriesMatch.name;
          _series = _seriesEnglish;
        }
        if (_seriesSpanish.isEmpty && seriesMatch.seriesSpanish.isNotEmpty) {
          _seriesSpanish = seriesMatch.seriesSpanish;
        }
        _onSeriesSelected(_seriesEnglish);
      }
    });
  }

  void _onTitleSpanishSelected(String selectedSpanishTitle) {
    final volMatch = widget.volumes.where((v) =>
        v.spanishTitle.toLowerCase() == selectedSpanishTitle.toLowerCase()).firstOrNull;

    final seriesMatch = widget.seriesList.where((s) =>
        s.seriesSpanish.toLowerCase() == selectedSpanishTitle.toLowerCase()).firstOrNull;

    setState(() {
      _titleSpanish = selectedSpanishTitle;

      if (volMatch != null) {
        if (_titleEnglish.isEmpty && volMatch.englishTitle.isNotEmpty) {
          _titleEnglish = volMatch.englishTitle;
          _title = volMatch.englishTitle;
        }
        if (_seriesEnglish.isEmpty && volMatch.seriesName != null && volMatch.seriesName!.isNotEmpty) {
          _seriesEnglish = volMatch.seriesName!;
          _series = volMatch.seriesName!;
        }
        if (_seriesSpanish.isEmpty && volMatch.seriesSpanish != null && volMatch.seriesSpanish!.isNotEmpty) {
          _seriesSpanish = volMatch.seriesSpanish!;
        }
      } else if (seriesMatch != null) {
        if (_titleEnglish.isEmpty) {
          _titleEnglish = seriesMatch.seriesEnglish.isNotEmpty ? seriesMatch.seriesEnglish : seriesMatch.name;
          _title = _titleEnglish;
        }
        if (_seriesSpanish.isEmpty) {
          _seriesSpanish = seriesMatch.seriesSpanish;
        }
        if (_seriesEnglish.isEmpty) {
          _seriesEnglish = seriesMatch.seriesEnglish.isNotEmpty ? seriesMatch.seriesEnglish : seriesMatch.name;
          _series = _seriesEnglish;
        }
      }
    });
  }

  BookMetadata _toBookMetadata() {
    return BookMetadata(
      identifier: _identifier,
      language: _bookLanguage,
      title: _titleEnglish.isNotEmpty ? _titleEnglish : _title,
      asin: _asin,
      isbn13: _isbn13,
      isbn10: _isbn10,
      series: _seriesEnglish.isNotEmpty ? _seriesEnglish : _series,
      seriesIndex: _volumeNumber,
      actors: _actors,
      publishers: _publishers,
      description: _description,
      originalLanguage: _originalLanguage,
      demographic: _demographic,
      genres: _selectedGenres.toList(),
      bookType: _bookType,
    );
  }

  void _applyAiSuggestion(ZeepubEditorialState state) {
    final s = state.latestAiSuggestion;
    if (s == null) return;
    setState(() {
      if (s.spanishTitle.isNotEmpty) {
        _titleSpanish = s.spanishTitle;
        _seriesSpanish = s.spanishTitle;
      }
      if (s.englishTitle.isNotEmpty) {
        _titleEnglish = s.englishTitle;
        _seriesEnglish = s.englishTitle;
      }
      if (s.author.isNotEmpty) {
        final existingAutIdx = _actors.indexWhere((a) => a.roles.contains(MarcRelator.aut));
        if (existingAutIdx >= 0) {
          _actors[existingAutIdx] = _actors[existingAutIdx].copyWith(name: s.author, fileAs: fileAsFor(s.author));
        } else {
          _actors.insert(0, Actor(name: s.author, roles: const [MarcRelator.aut], fileAs: fileAsFor(s.author)));
        }
      }
      if (s.volume != null) {
        _volumeNumber = s.volume! % 1 == 0 ? s.volume!.toInt().toString() : s.volume!.toString();
      }
      if (s.demography.isNotEmpty) {
        _demographic = Demographic.values.where((d) => d.name.toLowerCase() == s.demography.toLowerCase() || d.label.toLowerCase().contains(s.demography.toLowerCase())).firstOrNull ?? _demographic;
      }
    });
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        backgroundColor: Colors.green,
        content: Text('✨ Sugerencia de IA aplicada a los campos'),
      ),
    );
  }

  String _buildCoverUrl() {
    final rawCover = _customCoverUrl ?? widget.volume.coverUrl;
    if (rawCover == null || rawCover.isEmpty) return '';
    if (rawCover.startsWith('http')) return rawCover;
    final cleanBase = widget.baseUrl.replaceAll(RegExp(r'/+$'), '');
    final cleanPath = rawCover.startsWith('/') ? rawCover : '/$rawCover';
    return '$cleanBase$cleanPath';
  }

  Future<void> _pickAndUploadCover() async {
    final cubit = context.read<ZeepubEditorialCubit>();
    final files = await FilePicker.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['jpg', 'jpeg', 'png', 'webp'],
      dialogTitle: 'Seleccionar nueva portada para el tomo',
      windowsOptions: const WindowsOptions(lockParentWindow: true),
    );
    if (files.isNotEmpty) {
      final file = files.first;
      if (file.path != null) {
        final bytes = await File(file.path!).readAsBytes();
        final newUrl = await cubit.uploadCover(widget.volume.bookHash, bytes, file.name);
        if (newUrl != null && mounted) {
          setState(() {
            _customCoverUrl = newUrl;
          });
        }
      }
    }
  }

  void _showCustomUrlDialog() {
    final ctrl = TextEditingController(text: _customCoverUrl ?? widget.volume.coverUrl ?? '');
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.link_rounded),
            SizedBox(width: 8),
            Text('Cambiar URL de Portada'),
          ],
        ),
        content: TextField(
          controller: ctrl,
          decoration: const InputDecoration(
            labelText: 'URL de la imagen de portada',
            hintText: 'https://...',
            border: OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () {
              final val = ctrl.text.trim();
              if (val.isNotEmpty) {
                setState(() {
                  _customCoverUrl = val;
                });
                context.read<ZeepubEditorialCubit>().saveVolume(widget.volume.bookHash, {'cover_url': val});
              }
              Navigator.of(ctx).pop();
            },
            child: const Text('Aplicar URL'),
          ),
        ],
      ),
    );
  }

  Future<void> _handleSave() async {
    if (!_isStandalone && _seriesSpanish.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          backgroundColor: Colors.red,
          content: Text('El campo "Serie en español" es obligatorio'),
        ),
      );
      return;
    }
    if (_titleSpanish.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          backgroundColor: Colors.red,
          content: Text('El campo "Título en español" es obligatorio'),
        ),
      );
      return;
    }

    final cubit = context.read<ZeepubEditorialCubit>();
    final volNum = _isStandalone ? null : double.tryParse(_volumeNumber.trim());

    final primaryAuthor = _actors.where((a) => a.roles.contains(MarcRelator.aut)).firstOrNull?.name ?? '';
    final primaryIllustrator = _actors.where((a) => a.roles.contains(MarcRelator.ill)).firstOrNull?.name ?? '';
    final primaryTranslator = _actors.where((a) => a.roles.contains(MarcRelator.trl)).firstOrNull?.name ?? '';
    final primaryLayout = _actors.where((a) => a.roles.contains(MarcRelator.mrk)).firstOrNull?.name ?? '';
    final primaryPublisher = _publishers.where((p) => p.trim().isNotEmpty).join(', ');

    final payload = <String, dynamic>{
      'title': _titleEnglish.trim().isNotEmpty ? _titleEnglish.trim() : _title.trim(),
      'spanish_title': _titleSpanish.trim(),
      'english_title': _titleEnglish.trim(),
      'volume': volNum,
      'edition': _isStandalone ? 'Volumen Único' : (widget.volume.edition ?? ''),
      'color_mode': _colorMode,
      'is_uncensored': _isUncensored,
      'author': primaryAuthor.trim(),
      'illustrator': primaryIllustrator.trim(),
      'translator': primaryTranslator.trim(),
      'layout_by': primaryLayout.trim(),
      'publisher': primaryPublisher.trim(),
      'description': _description.trim(),
      'demography': _demographic?.name ?? 'General',
      if (_customCoverUrl != null) 'cover_url': _customCoverUrl,
    };

    await cubit.saveVolume(widget.volume.bookHash, payload);
  }

  void _openPublishDialog() {
    context.read<ZeepubEditorialCubit>().openPublisher(widget.volume);
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final tt = Theme.of(context).textTheme;
    final coverUrl = _buildCoverUrl();

    final asinField = AppTextField(
      label: 'ASIN de Amazon',
      value: _asin,
      hint: 'B0XXXXXXXX',
      onChanged: (v) => setState(() => _asin = v.trim().toUpperCase()),
    );

    return BlocConsumer<ZeepubEditorialCubit, ZeepubEditorialState>(
      listener: (BuildContext context, ZeepubEditorialState state) {
        if (state.latestAiSuggestion != null) {
          _applyAiSuggestion(state);
        }
      },
      builder: (BuildContext context, ZeepubEditorialState state) {
        final cubit = context.read<ZeepubEditorialCubit>();

        return Scaffold(
          appBar: AppBar(
            leading: IconButton(
              icon: const Icon(Icons.arrow_back),
              tooltip: 'Volver a Tomos',
              onPressed: widget.onBack,
            ),
            title: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  widget.volume.englishTitle.isNotEmpty
                      ? widget.volume.englishTitle
                      : (widget.volume.seriesName ?? widget.volume.title),
                  style: tt.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                ),
                Text(
                  widget.volume.volume != null
                      ? 'Volumen ${widget.volume.volume! % 1 == 0 ? widget.volume.volume!.toInt() : widget.volume.volume}'
                      : (widget.volume.edition ?? 'Volumen'),
                  style: tt.bodySmall?.copyWith(color: cs.onSurfaceVariant),
                ),
              ],
            ),
            actions: [
              IconButton.filledTonal(
                icon: state.aiLoading
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.auto_awesome),
                tooltip: 'Sugerir con IA (Gemini)',
                onPressed: state.aiLoading
                    ? null
                    : () => cubit.requestAiSuggestion(
                          _titleEnglish.isNotEmpty ? _titleEnglish : (_title.isNotEmpty ? _title : widget.volume.title),
                        ),
              ),
              const SizedBox(width: 8),
              FilledButton.icon(
                icon: const Icon(Icons.send_rounded, size: 18),
                label: const Text('Publicar'),
                style: FilledButton.styleFrom(
                  backgroundColor: Colors.blue.shade700,
                  foregroundColor: Colors.white,
                ),
                onPressed: _openPublishDialog,
              ),
              const SizedBox(width: 8),
              FilledButton.icon(
                icon: state.saving
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Icon(Icons.save_rounded, size: 18),
                label: const Text('Guardar'),
                onPressed: state.saving ? null : _handleSave,
              ),
              const SizedBox(width: 16),
            ],
          ),
          body: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // LEFT PANEL: Resizable Cover, File Info, Quick Actions
              SizedBox(
                width: _leftPanelWidth,
                child: Container(
                  padding: const EdgeInsets.all(AppPadding.large),
                  decoration: BoxDecoration(
                    border: Border(right: BorderSide(color: cs.outlineVariant.withValues(alpha: 0.3))),
                  ),
                  child: ListView(
                    children: [
                      // Cover Image Container (Responsive to width)
                      Center(
                        child: Container(
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(AppRadius.medium),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withValues(alpha: 0.35),
                                blurRadius: 12,
                                offset: const Offset(0, 4),
                              ),
                            ],
                          ),
                          child: ClipRRect(
                            borderRadius: BorderRadius.circular(AppRadius.medium),
                            child: AspectRatio(
                              aspectRatio: 0.7,
                              child: coverUrl.isNotEmpty
                                  ? Image.network(
                                      coverUrl,
                                      fit: BoxFit.cover,
                                      errorBuilder: (context, error, stack) => Container(
                                        color: cs.surfaceContainerHighest,
                                        child: const Icon(Icons.broken_image, size: 48),
                                      ),
                                    )
                                  : Container(
                                      color: cs.surfaceContainerHighest,
                                      child: const Icon(Icons.book, size: 48),
                                    ),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),

                      // Change Cover Buttons
                      Row(
                        children: [
                          Expanded(
                            child: FilledButton.tonalIcon(
                              icon: const Icon(Icons.photo_camera_rounded, size: 16),
                              label: const Text('Cambiar Portada', style: TextStyle(fontSize: 12)),
                              onPressed: state.saving ? null : _pickAndUploadCover,
                            ),
                          ),
                          const SizedBox(width: 6),
                          IconButton.outlined(
                            tooltip: 'Pegar URL de Imagen',
                            icon: const Icon(Icons.link_rounded, size: 16),
                            onPressed: _showCustomUrlDialog,
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),

                      // File info
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        spacing: 8,
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  'Hash: ${widget.volume.bookHash.length > 12 ? widget.volume.bookHash.substring(0, 12) : widget.volume.bookHash}...',
                                  style: tt.labelSmall?.copyWith(fontFamily: 'monospace', color: cs.onSurfaceVariant),
                                ),
                              ),
                              IconButton(
                                tooltip: 'Copiar Hash',
                                icon: const Icon(Icons.copy_rounded, size: 16),
                                onPressed: () {
                                  Clipboard.setData(ClipboardData(text: widget.volume.bookHash));
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(content: Text('Hash copiado al portapapeles')),
                                  );
                                },
                              ),
                            ],
                          ),
                          if (widget.volume.fileSize != null)
                            Text(
                              'Tamaño: ${(widget.volume.fileSize! / (1024 * 1024)).toStringAsFixed(2)} MB',
                              style: tt.bodySmall,
                            ),
                          if (widget.volume.filepath != null)
                            Text(
                              'Ruta en Servidor: ${widget.volume.filepath ?? ""}',
                              style: tt.labelSmall?.copyWith(color: cs.onSurfaceVariant),
                            ),
                          const SizedBox(height: 8),
                          OutlinedButton.icon(
                            icon: const Icon(Icons.sync_rounded, size: 16),
                            label: const Text('Re-escanear EPUB en disco'),
                            onPressed: state.saving
                                ? null
                                : () => cubit.syncVolumeFromDisk(widget.volume.bookHash),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),

              // DRAGGABLE VERTICAL SPLITTER
              MouseRegion(
                cursor: SystemMouseCursors.resizeColumn,
                child: GestureDetector(
                  behavior: HitTestBehavior.translucent,
                  onHorizontalDragUpdate: (details) {
                    setState(() {
                      _leftPanelWidth = (_leftPanelWidth + details.delta.dx).clamp(200.0, 650.0);
                    });
                  },
                  child: Container(
                    width: 12,
                    color: Colors.transparent,
                    child: Center(
                      child: Container(
                        width: 3,
                        height: 50,
                        decoration: BoxDecoration(
                          color: cs.outlineVariant.withValues(alpha: 0.7),
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                  ),
                ),
              ),

              // RIGHT PANEL: Comprehensive Metadata Editor Form (matching ZeeTools MetadataForm)
              Expanded(
                child: ListView(
                  padding: const EdgeInsets.fromLTRB(AppPadding.large, AppPadding.large, AppPadding.large, 96),
                  children: [
                    // SECTION 1: IDENTIFICADORES
                    FormSection(
                      title: 'Identificadores',
                      children: [
                        AmazonLookup(
                          asin: _asin,
                          metadata: _toBookMetadata(),
                          onApply: (updater) {
                            setState(() {
                              final updated = updater(_toBookMetadata());
                              _asin = updated.asin;
                              _isbn13 = updated.isbn13;
                              _isbn10 = updated.isbn10;
                              if (updated.altTitles.isNotEmpty) {
                                final jaTitle = updated.altTitles.where((t) => t.lang.toLowerCase() == 'ja').firstOrNull?.text;
                                if (jaTitle != null && jaTitle.isNotEmpty) _titleNative = jaTitle;
                              }
                              if (updated.altSeries.isNotEmpty) {
                                final jaSeries = updated.altSeries.where((t) => t.lang.toLowerCase() == 'ja').firstOrNull?.text;
                                if (jaSeries != null && jaSeries.isNotEmpty) _seriesNative = jaSeries;
                              }
                              if (updated.actors.isNotEmpty) {
                                _actors = [...updated.actors];
                              }
                            });
                          },
                          field: asinField,
                        ),
                        ResponsiveRow(
                          children: [
                            AppTextField(
                              label: 'ISBN-13',
                              value: _isbn13,
                              hint: '978-XX-XXXX-XXX-X',
                              inputFormatters: [isbnFormatter(isbn13Groups)],
                              error: _isbn13.trim().isNotEmpty && !isValidIsbn13(_isbn13) ? 'ISBN-13 no válido' : null,
                              onChanged: (v) => setState(() {
                                _isbn13 = v;
                                if (isbn10From13(v) case final ten? when _isbn10.trim().isEmpty) {
                                  _isbn10 = formatIsbn(ten, isbn10Groups);
                                }
                              }),
                            ),
                            AppTextField(
                              label: 'ISBN-10',
                              value: _isbn10,
                              hint: 'XX-XXXX-XXX-X',
                              inputFormatters: [isbnFormatter(isbn10Groups)],
                              error: _isbn10.trim().isNotEmpty && !isValidIsbn10(_isbn10) ? 'ISBN-10 no válido' : null,
                              onChanged: (v) => setState(() {
                                _isbn10 = v;
                                if (isbn13From10(v) case final thirteen? when _isbn13.trim().isEmpty) {
                                  _isbn13 = formatIsbn(thirteen, isbn13Groups);
                                }
                              }),
                            ),
                          ],
                        ),
                        Row(
                          children: [
                            Expanded(
                              child: InputDecorator(
                                decoration: const InputDecoration(labelText: 'Identificador único (UUID)'),
                                child: SelectableText('urn:uuid:$_identifier'),
                              ),
                            ),
                            IconButton(
                              tooltip: 'Copiar Identificador',
                              icon: const Icon(Icons.copy, size: 18),
                              onPressed: () => Clipboard.setData(ClipboardData(text: 'urn:uuid:$_identifier')),
                            ),
                            IconButton(
                              tooltip: 'Generar nuevo UUID',
                              icon: const Icon(Icons.refresh, size: 18),
                              onPressed: () => setState(() => _identifier = uuidV7()),
                            ),
                          ],
                        ),
                      ],
                    ),

                    // SECTION 2: SERIE Y TÍTULO
                    FormSection(
                      title: 'Serie y título',
                      children: [
                        OutlinedDropdown<OriginalLanguage?>(
                          label: 'Idioma en que se escribió la obra',
                          value: _originalLanguage,
                          helper: switch (_originalLanguage) {
                            OriginalLanguage.es => 'El título y la serie principales van en español; en inglés son opcionales.',
                            OriginalLanguage(scripted: true) => 'Añade el título y la serie romanizados y en su escritura nativa.',
                            _ => null,
                          },
                          onChanged: (v) => setState(() => _originalLanguage = v),
                          items: [
                            for (final o in OriginalLanguage.values)
                              DropdownMenuItem(value: o, child: Text(o.label)),
                          ],
                        ),
                        ToggleField(
                          label: 'Volumen único',
                          value: _isStandalone,
                          helper: 'No pertenece a ninguna serie: no lleva serie ni número de volumen.',
                          onChanged: (v) => setState(() {
                            _isStandalone = v;
                            if (v) _volumeNumber = '';
                          }),
                        ),
                        if (!_isStandalone) ...[
                          ResponsiveRow(
                            widths: const [null, numberColumnWidth],
                            children: [
                              Autocomplete<String>(
                                initialValue: TextEditingValue(text: _seriesEnglish.isNotEmpty ? _seriesEnglish : _series),
                                optionsBuilder: (textEditingValue) {
                                  if (textEditingValue.text.isEmpty) {
                                    return widget.seriesList.map((s) => s.seriesEnglish.isNotEmpty ? s.seriesEnglish : s.name);
                                  }
                                  final query = textEditingValue.text.toLowerCase();
                                  return widget.seriesList
                                      .where((s) =>
                                          s.seriesEnglish.toLowerCase().contains(query) ||
                                          s.name.toLowerCase().contains(query) ||
                                          s.seriesSpanish.toLowerCase().contains(query))
                                      .map((s) => s.seriesEnglish.isNotEmpty ? s.seriesEnglish : s.name);
                                },
                                onSelected: _onSeriesSelected,
                                fieldViewBuilder: (context, controller, focusNode, onFieldSubmitted) {
                                  return TextField(
                                    controller: controller,
                                    focusNode: focusNode,
                                    decoration: const InputDecoration(
                                      labelText: 'Serie en inglés / principal',
                                      hintText: 'English Series Name',
                                    ),
                                    onChanged: (v) {
                                      setState(() {
                                        _seriesEnglish = v;
                                        _series = v;
                                      });
                                      final match = widget.seriesList.where((s) =>
                                          s.seriesEnglish.toLowerCase() == v.trim().toLowerCase() ||
                                          s.name.toLowerCase() == v.trim().toLowerCase()).firstOrNull;
                                      if (match != null) {
                                        _onSeriesSelected(v.trim());
                                      }
                                    },
                                  );
                                },
                              ),
                              AppTextField(
                                label: 'Volumen',
                                value: _volumeNumber,
                                hint: '1',
                                inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d*'))],
                                onChanged: (v) => setState(() => _volumeNumber = v),
                              ),
                            ],
                          ),
                          ResponsiveRow(
                            children: [
                              Autocomplete<String>(
                                initialValue: TextEditingValue(text: _seriesSpanish),
                                optionsBuilder: (textEditingValue) {
                                  final allSpaSeries = <String>{};
                                  for (final s in widget.seriesList) {
                                    if (s.seriesSpanish.isNotEmpty) allSpaSeries.add(s.seriesSpanish);
                                  }
                                  for (final v in widget.volumes) {
                                    if (v.spanishTitle.isNotEmpty) allSpaSeries.add(v.spanishTitle);
                                  }
                                  if (textEditingValue.text.isEmpty) {
                                    return allSpaSeries;
                                  }
                                  final query = textEditingValue.text.toLowerCase();
                                  return allSpaSeries.where((s) => s.toLowerCase().contains(query));
                                },
                                onSelected: (val) {
                                  setState(() {
                                    _seriesSpanish = val;
                                  });
                                  _onSeriesSelected(val);
                                },
                                fieldViewBuilder: (context, controller, focusNode, onFieldSubmitted) {
                                  return TextField(
                                    controller: controller,
                                    focusNode: focusNode,
                                    decoration: InputDecoration(
                                      labelText: 'Serie en español',
                                      hintText: 'Nombre de la serie en español',
                                      errorText: (!_isStandalone && _seriesSpanish.trim().isEmpty) ? 'Obligatorio' : null,
                                    ),
                                    onChanged: (v) => setState(() => _seriesSpanish = v),
                                  );
                                },
                              ),
                              if (_originalLanguage != null && _originalLanguage!.scripted) ...[
                                AppTextField(
                                  label: 'Serie en ${_originalLanguage!.romanization}',
                                  value: _seriesRomaji,
                                  hint: 'Romaji / Romanizado',
                                  onChanged: (v) => setState(() => _seriesRomaji = v),
                                ),
                                AppTextField(
                                  label: 'Serie en ${_originalLanguage!.label.toLowerCase()}',
                                  value: _seriesNative,
                                  hint: 'Caracteres nativos (Kanji/Hangul/Hanzi)',
                                  onChanged: (v) => setState(() => _seriesNative = v),
                                ),
                              ],
                            ],
                          ),
                        ],
                        Autocomplete<String>(
                          initialValue: TextEditingValue(text: _titleEnglish.isNotEmpty ? _titleEnglish : _title),
                          optionsBuilder: (textEditingValue) {
                            final allTitles = <String>{};
                            for (final v in widget.volumes) {
                              if (v.englishTitle.isNotEmpty) allTitles.add(v.englishTitle);
                              if (v.title.isNotEmpty) allTitles.add(v.title);
                            }
                            for (final s in widget.seriesList) {
                              if (s.seriesEnglish.isNotEmpty) allTitles.add(s.seriesEnglish);
                              if (s.name.isNotEmpty) allTitles.add(s.name);
                            }
                            if (textEditingValue.text.isEmpty) {
                              return allTitles;
                            }
                            final query = textEditingValue.text.toLowerCase();
                            return allTitles.where((t) => t.toLowerCase().contains(query));
                          },
                          onSelected: _onTitleEnglishSelected,
                          fieldViewBuilder: (context, controller, focusNode, onFieldSubmitted) {
                            return TextField(
                              controller: controller,
                              focusNode: focusNode,
                              decoration: const InputDecoration(
                                labelText: 'Título en inglés / principal',
                                hintText: 'English Title',
                              ),
                              onChanged: (v) {
                                setState(() {
                                  _titleEnglish = v;
                                  _title = v;
                                });
                                final match = widget.volumes.where((vol) =>
                                    vol.englishTitle.toLowerCase() == v.trim().toLowerCase() ||
                                    vol.title.toLowerCase() == v.trim().toLowerCase()).firstOrNull;
                                if (match != null) {
                                  _onTitleEnglishSelected(v.trim());
                                }
                              },
                            );
                          },
                        ),
                        ResponsiveRow(
                          children: [
                            Autocomplete<String>(
                              initialValue: TextEditingValue(text: _titleSpanish),
                              optionsBuilder: (textEditingValue) {
                                final allSpaTitles = <String>{};
                                for (final v in widget.volumes) {
                                  if (v.spanishTitle.isNotEmpty) allSpaTitles.add(v.spanishTitle);
                                }
                                for (final s in widget.seriesList) {
                                  if (s.seriesSpanish.isNotEmpty) allSpaTitles.add(s.seriesSpanish);
                                }
                                if (textEditingValue.text.isEmpty) {
                                  return allSpaTitles;
                                }
                                final query = textEditingValue.text.toLowerCase();
                                return allSpaTitles.where((t) => t.toLowerCase().contains(query));
                              },
                              onSelected: _onTitleSpanishSelected,
                              fieldViewBuilder: (context, controller, focusNode, onFieldSubmitted) {
                                return TextField(
                                  controller: controller,
                                  focusNode: focusNode,
                                  decoration: InputDecoration(
                                    labelText: 'Título en español',
                                    hintText: 'Título en español',
                                    errorText: _titleSpanish.trim().isEmpty ? 'Obligatorio' : null,
                                  ),
                                  onChanged: (v) {
                                    setState(() => _titleSpanish = v);
                                    final match = widget.volumes.where((vol) =>
                                        vol.spanishTitle.toLowerCase() == v.trim().toLowerCase()).firstOrNull;
                                    if (match != null) {
                                      _onTitleSpanishSelected(v.trim());
                                    }
                                  },
                                );
                              },
                            ),
                            if (_originalLanguage != null && _originalLanguage!.scripted) ...[
                              AppTextField(
                                label: 'Título en ${_originalLanguage!.romanization}',
                                value: _titleRomaji,
                                hint: 'Romaji / Romanizado',
                                onChanged: (v) => setState(() => _titleRomaji = v),
                              ),
                              AppTextField(
                                label: 'Título en ${_originalLanguage!.label.toLowerCase()}',
                                value: _titleNative,
                                hint: 'Caracteres nativos (Kanji/Hangul/Hanzi)',
                                onChanged: (v) => setState(() => _titleNative = v),
                              ),
                            ],
                          ],
                        ),
                        AppTextField(
                          label: 'Título para ordenar (Opcional)',
                          value: _titleSort,
                          hint: 'Titulo para ordenar alfabeticamente',
                          onChanged: (v) => setState(() => _titleSort = v),
                        ),
                      ],
                    ),

                    // SECTION 3: PERSONAS (Matching native ZeeTools _ActorEditor & EditableList)
                    FormSection(
                      title: 'Personas',
                      children: [
                        EditableList<Actor>(
                          items: _actors,
                          addLabel: 'Añadir persona',
                          createItem: () => const Actor(roles: [MarcRelator.ctb]),
                          onChanged: (v) => setState(() => _actors = v),
                          itemBuilder: (context, actor, onChanged, controls) => _ActorEditor(
                            actor: actor,
                            onChanged: onChanged,
                            controls: controls,
                            defaultScript: _originalLanguage != null && _originalLanguage!.scripted
                                ? _originalLanguage!
                                : OriginalLanguage.ja,
                          ),
                        ),
                      ],
                    ),

                    // SECTION 4: PUBLICACIÓN (Separated section with multiple publishers and book details)
                    FormSection(
                      title: 'Publicación',
                      children: [
                        ResponsiveRow(
                          children: [
                            OutlinedDropdown<String>(
                              label: 'Idioma del libro',
                              value: _bookLanguage,
                              onChanged: (v) {
                                if (v != null) setState(() => _bookLanguage = v);
                              },
                              items: [
                                for (final MapEntry(key: code, value: name) in bookLanguages.entries)
                                  DropdownMenuItem(value: code, child: Text(name)),
                              ],
                            ),
                            _BookTypeField(
                              value: _bookType,
                              onChanged: (v) => setState(() => _bookType = v),
                            ),
                          ],
                        ),
                        ResponsiveRow(
                          children: [
                            AppTextField(
                              label: 'Fecha de publicación',
                              value: _publishDate,
                              hint: 'AAAA-MM-DD',
                              onChanged: (v) => setState(() => _publishDate = v),
                            ),
                            Row(
                              children: [
                                Expanded(
                                  child: OutlinedDropdown<String>(
                                    label: 'Modo de Color',
                                    value: _colorMode,
                                    onChanged: (v) {
                                      if (v != null) setState(() => _colorMode = v);
                                    },
                                    items: const [
                                      DropdownMenuItem(value: 'mono', child: Text('Monocromo (B/N)')),
                                      DropdownMenuItem(value: 'color', child: Text('Ilustraciones a Color')),
                                    ],
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: CheckboxListTile(
                                    value: _isUncensored,
                                    title: const Text('Sin Censura (+18)', style: TextStyle(fontSize: 12)),
                                    dense: true,
                                    contentPadding: EdgeInsets.zero,
                                    controlAffinity: ListTileControlAffinity.leading,
                                    onChanged: (v) => setState(() => _isUncensored = v ?? false),
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                        EditableList<String>(
                          items: _publishers,
                          addLabel: 'Añadir editorial o fansub',
                          createItem: () => '',
                          onChanged: (v) => setState(() => _publishers = v),
                          itemBuilder: (context, publisher, onChanged, controls) => EditableRow(
                            controls: controls,
                            child: AppTextField(
                              label: 'Editorial / Fansub',
                              value: publisher,
                              hint: 'Nombre de la editorial o grupo traductor',
                              onChanged: onChanged,
                            ),
                          ),
                        ),
                      ],
                    ),

                    // SECTION 5: SINOPSIS
                    FormSection(
                      title: 'Sinopsis',
                      children: [
                        AppTextField(
                          label: 'Sinopsis',
                          value: _description,
                          hint: 'Descripción o sinopsis del tomo...',
                          maxLines: 8,
                          onChanged: (v) => setState(() => _description = v),
                        ),
                      ],
                    ),

                    // SECTION 6: CLASIFICACIÓN
                    FormSection(
                      title: 'Clasificación',
                      children: [
                        Row(
                          children: [
                            Text('Demografía:', style: tt.labelMedium?.copyWith(color: cs.onSurfaceVariant)),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Wrap(
                                spacing: 8,
                                runSpacing: 8,
                                children: [
                                  for (final d in Demographic.values)
                                    SelectionPill(
                                      label: d.label,
                                      selected: _demographic == d,
                                      onSelected: (selected) => setState(() => _demographic = selected ? d : null),
                                    ),
                                ],
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Géneros:', style: tt.labelMedium?.copyWith(color: cs.onSurfaceVariant)),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Wrap(
                                spacing: 6,
                                runSpacing: 6,
                                children: [
                                  for (final s in Subject.values)
                                    TagPill(
                                      label: s.label,
                                      selected: _selectedGenres.contains(s),
                                      onSelected: (selected) => setState(() {
                                        if (selected) {
                                          _selectedGenres.add(s);
                                        } else {
                                          _selectedGenres.remove(s);
                                        }
                                      }),
                                    ),
                                ],
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            Text('Calificación:', style: tt.labelMedium?.copyWith(color: cs.onSurfaceVariant)),
                            const SizedBox(width: 12),
                            for (int i = 1; i <= 5; i++)
                              IconButton(
                                icon: Icon(
                                  _rating != null && _rating! >= i ? Icons.star_rounded : Icons.star_border_rounded,
                                  color: Colors.amber,
                                  size: 22,
                                ),
                                onPressed: () => setState(() => _rating = _rating == i ? null : i),
                              ),
                          ],
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _ActorEditor extends StatelessWidget {
  final Actor actor;
  final ValueChanged<Actor> onChanged;
  final Widget controls;
  final OriginalLanguage defaultScript;

  const _ActorEditor({
    required this.actor,
    required this.onChanged,
    required this.controls,
    required this.defaultScript,
  });

  @override
  Widget build(BuildContext context) {
    return EditableRow(
      controls: controls,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          ResponsiveRow(
            widths: const [null, 160],
            children: [
              AppTextField(
                label: 'Nombre',
                value: actor.name,
                hint: 'Nombre de la persona',
                onChanged: (v) => onChanged(actor.copyWith(name: v, fileAs: fileAsFor(v))),
              ),
              OutlinedDropdown<MarcRelator>(
                label: 'Rol',
                value: actor.roles.isNotEmpty ? actor.roles.first : MarcRelator.aut,
                onChanged: (r) {
                  if (r != null) onChanged(actor.copyWith(roles: [r]));
                },
                items: [
                  for (final r in MarcRelator.values)
                    DropdownMenuItem(value: r, child: Text(r.label)),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _BookTypeField extends StatelessWidget {
  final BookType value;
  final ValueChanged<BookType> onChanged;

  const _BookTypeField({required this.value, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return OutlinedDropdown<BookType>(
      label: 'Tipo de libro',
      value: value,
      onChanged: (v) {
        if (v != null) onChanged(v);
      },
      items: [
        for (final t in BookType.values)
          DropdownMenuItem(value: t, child: Text(t.label)),
      ],
    );
  }
}
''')

print("Successfully wrote clean full files!")
