# -*- coding: utf-8 -*-
import os

base_dir = r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial"
datasources_dir = os.path.join(base_dir, "data", "datasources")
repositories_dir = os.path.join(base_dir, "data", "repositories")
cubit_dir = os.path.join(base_dir, "presentation", "cubit")
views_dir = os.path.join(base_dir, "presentation", "views")
widgets_dir = os.path.join(views_dir, "widgets")

# 1. API Client
api_client_code = r'''import 'dart:convert';
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

    final jsonString = jsonEncode(body);
    request.write(jsonString);

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

    final jsonString = jsonEncode(body);
    request.write(jsonString);

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
    if (query != null && query.trim().isNotEmpty) params['query'] = query.trim();
    if (seriesId != null && seriesId.trim().isNotEmpty) params['series_id'] = seriesId.trim();
    if (workgroupId != null) params['workgroup_id'] = workgroupId.toString();
    if (colorMode != null && colorMode.trim().isNotEmpty) params['color_mode'] = colorMode.trim();
    if (isUncensored != null) params['is_uncensored'] = isUncensored.toString();

    final data = await _get('/api/editorial/volumes', params);
    final rawList = (data['items'] as List<dynamic>?) ?? [];
    final items = rawList.map((e) => ZeepubVolume.fromJson(e as Map<String, dynamic>)).toList();
    final total = (data['total'] as num?)?.toInt() ?? items.length;
    final totalPages = (data['total_pages'] as num?)?.toInt() ?? 1;

    return (items: items, total: total, page: page, totalPages: totalPages);
  }

  Future<ZeepubVolume> getVolumeDetail(String bookHash) async {
    final data = await _get('/api/editorial/volume/$bookHash');
    final bookData = data['book'] as Map<String, dynamic>? ?? data;
    return ZeepubVolume.fromJson(bookData);
  }

  Future<void> updateVolume(String bookHash, Map<String, dynamic> payload) async {
    await _put('/api/editorial/volume/$bookHash', payload);
  }

  Future<Map<String, dynamic>> syncVolumeFile(String bookHash) async {
    return await _post('/api/editorial/volume/$bookHash/sync-file', {});
  }

  // --- Series ---

  Future<({List<ZeepubSeries> items, int total, int page})> getSeriesList({
    int page = 1,
    int pageSize = 50,
    String? query,
  }) async {
    final params = <String, String>{
      'page': page.toString(),
      'page_size': pageSize.toString(),
    };
    if (query != null && query.trim().isNotEmpty) params['query'] = query.trim();

    final data = await _get('/api/editorial/series', params);
    final rawList = (data['items'] as List<dynamic>?) ?? [];
    final items = rawList.map((e) => ZeepubSeries.fromJson(e as Map<String, dynamic>)).toList();
    final total = (data['total'] as num?)?.toInt() ?? items.length;

    return (items: items, total: total, page: page);
  }

  Future<Map<String, dynamic>> getSeriesDetail(String seriesId) async {
    return await _get('/api/editorial/series/$seriesId');
  }

  Future<void> updateSeries(String seriesId, Map<String, dynamic> payload) async {
    await _put('/api/editorial/series/$seriesId', payload);
  }

  // --- Workgroups ---

  Future<List<ZeepubWorkgroup>> getWorkgroups() async {
    final raw = await _getRaw('/api/editorial/groups');
    if (raw is List) {
      return raw.map((e) => ZeepubWorkgroup.fromJson(e as Map<String, dynamic>)).toList();
    }
    return [];
  }

  // --- AI Suggest ---

  Future<ZeepubAiSuggestion?> aiSuggestMetadata(String title) async {
    final data = await _post('/api/editorial/ai/suggest', {'title': title});
    if (data['success'] == true && data['metadata'] != null) {
      return ZeepubAiSuggestion.fromJson(data['metadata'] as Map<String, dynamic>);
    }
    return null;
  }

  // --- Channels ---

  Future<List<ZeepubChannel>> getChannels() async {
    final data = await _get('/api/editorial/channels');
    final rawList = (data['channels'] as List<dynamic>?) ?? (data['items'] as List<dynamic>?) ?? [];
    return rawList.map((e) => ZeepubChannel.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<void> saveChannel(Map<String, dynamic> payload) async {
    await _post('/api/editorial/channels', payload);
  }

  Future<void> deleteChannel(int channelId) async {
    await _delete('/api/editorial/channels/$channelId');
  }

  // --- Templates ---

  Future<List<ZeepubTemplate>> getTemplates({String? platform}) async {
    final params = platform != null ? {'platform': platform} : null;
    final data = await _get('/api/editorial/templates', params);
    final rawList = (data['templates'] as List<dynamic>?) ?? (data['items'] as List<dynamic>?) ?? [];
    return rawList.map((e) => ZeepubTemplate.fromJson(e as Map<String, dynamic>)).toList();
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

  Future<List<ZeepubQueueItem>> getQueue({String? status, int limit = 100}) async {
    final params = <String, String>{'limit': limit.toString()};
    if (status != null && status.isNotEmpty) params['status'] = status;
    final data = await _get('/api/editorial/queue', params);
    final rawList = (data['items'] as List<dynamic>?) ?? (data['queue'] as List<dynamic>?) ?? [];
    return rawList.map((e) => ZeepubQueueItem.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<void> cancelQueueItem(int id) async {
    await _post('/api/editorial/queue/cancel', {'id': id});
  }

  Future<void> retryQueueItem(int id) async {
    await _post('/api/editorial/queue/retry', {'id': id});
  }

  // --- Posts History ---

  Future<List<ZeepubPostItem>> getPostsHistory({int limit = 100}) async {
    final data = await _get('/api/editorial/posts', {'limit': limit.toString()});
    final rawList = (data['items'] as List<dynamic>?) ?? (data['posts'] as List<dynamic>?) ?? [];
    return rawList.map((e) => ZeepubPostItem.fromJson(e as Map<String, dynamic>)).toList();
  }

  // --- Publication Actions ---

  Future<Map<String, dynamic>> publishNow({
    required String bookHash,
    int? channelId,
    int? templateId,
    String? customCaption,
    bool sendAsFile = true,
  }) async {
    return await _post('/api/editorial/publish/now', {
      'book_hash': bookHash,
      if (channelId != null) 'channel_id': channelId,
      if (templateId != null) 'template_id': templateId,
      if (customCaption != null) 'custom_caption': customCaption,
      'send_as_file': sendAsFile,
    });
  }

  Future<Map<String, dynamic>> schedulePublication({
    required String bookHash,
    required String scheduledAtIso,
    int? channelId,
    int? templateId,
    String? customCaption,
    bool sendAsFile = true,
  }) async {
    return await _post('/api/editorial/publish/schedule', {
      'book_hash': bookHash,
      'scheduled_for': scheduledAtIso,
      if (channelId != null) 'channel_id': channelId,
      if (templateId != null) 'template_id': templateId,
      if (customCaption != null) 'custom_caption': customCaption,
      'send_as_file': sendAsFile,
    });
  }
}
'''

# 2. Repository
repository_code = r'''import '/features/zeepub_editorial/data/datasources/zeepub_api_client.dart';
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

  Future<Map<String, dynamic>> syncVolumeFile(String bookHash) => _client.syncVolumeFile(bookHash);

  Future<({List<ZeepubSeries> items, int total, int page})> getSeriesList({
    int page = 1,
    int pageSize = 50,
    String? query,
  }) =>
      _client.getSeriesList(page: page, pageSize: pageSize, query: query);

  Future<Map<String, dynamic>> getSeriesDetail(String seriesId) => _client.getSeriesDetail(seriesId);

  Future<void> updateSeries(String seriesId, Map<String, dynamic> payload) => _client.updateSeries(seriesId, payload);

  Future<List<ZeepubWorkgroup>> getWorkgroups() => _client.getWorkgroups();

  Future<ZeepubAiSuggestion?> aiSuggestMetadata(String title) => _client.aiSuggestMetadata(title);

  // Channels
  Future<List<ZeepubChannel>> getChannels() => _client.getChannels();
  Future<void> saveChannel(Map<String, dynamic> payload) => _client.saveChannel(payload);
  Future<void> deleteChannel(int id) => _client.deleteChannel(id);

  // Templates
  Future<List<ZeepubTemplate>> getTemplates({String? platform}) => _client.getTemplates(platform: platform);
  Future<void> saveTemplate(Map<String, dynamic> payload) => _client.saveTemplate(payload);
  Future<void> deleteTemplate(int id) => _client.deleteTemplate(id);
  Future<void> restoreTemplates() => _client.restoreTemplates();

  // Queue
  Future<List<ZeepubQueueItem>> getQueue({String? status, int limit = 100}) => _client.getQueue(status: status, limit: limit);
  Future<void> cancelQueueItem(int id) => _client.cancelQueueItem(id);
  Future<void> retryQueueItem(int id) => _client.retryQueueItem(id);

  // Posts
  Future<List<ZeepubPostItem>> getPostsHistory({int limit = 100}) => _client.getPostsHistory(limit: limit);

  // Publications
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
'''

# 3. State
state_code = r'''import '/features/zeepub_editorial/data/models/zeepub_ai_suggestion.dart';
import '/features/zeepub_editorial/data/models/zeepub_channel.dart';
import '/features/zeepub_editorial/data/models/zeepub_post_item.dart';
import '/features/zeepub_editorial/data/models/zeepub_queue_item.dart';
import '/features/zeepub_editorial/data/models/zeepub_series.dart';
import '/features/zeepub_editorial/data/models/zeepub_template.dart';
import '/features/zeepub_editorial/data/models/zeepub_volume.dart';
import '/features/zeepub_editorial/data/models/zeepub_workgroup.dart';

class ZeepubEditorialState {
  final bool loading;
  final bool saving;
  final bool aiLoading;
  final String? errorMessage;
  final String? successMessage;

  // Volumes
  final List<ZeepubVolume> volumes;
  final int totalVolumes;
  final int currentPage;
  final int totalPages;
  final String searchQuery;
  final String? selectedSeriesId;
  final int? selectedWorkgroupId;
  final String? selectedColorMode;
  final bool? filterUncensored;

  // Series & Workgroups
  final List<ZeepubSeries> seriesList;
  final int totalSeries;
  final List<ZeepubWorkgroup> workgroups;

  // Publisher, Channels & Templates
  final List<ZeepubChannel> channels;
  final List<ZeepubTemplate> templates;
  final List<ZeepubQueueItem> queue;
  final List<ZeepubPostItem> posts;

  // Active View Models
  final ZeepubVolume? activeVolume;
  final ZeepubVolume? publishingVolume;
  final ZeepubAiSuggestion? latestAiSuggestion;
  final String baseUrl;

  const ZeepubEditorialState({
    this.loading = false,
    this.saving = false,
    this.aiLoading = false,
    this.errorMessage,
    this.successMessage,
    this.volumes = const [],
    this.totalVolumes = 0,
    this.currentPage = 1,
    this.totalPages = 1,
    this.searchQuery = '',
    this.selectedSeriesId,
    this.selectedWorkgroupId,
    this.selectedColorMode,
    this.filterUncensored,
    this.seriesList = const [],
    this.totalSeries = 0,
    this.workgroups = const [],
    this.channels = const [],
    this.templates = const [],
    this.queue = const [],
    this.posts = const [],
    this.activeVolume,
    this.publishingVolume,
    this.latestAiSuggestion,
    this.baseUrl = 'http://localhost:8001',
  });

  ZeepubEditorialState copyWith({
    bool? loading,
    bool? saving,
    bool? aiLoading,
    String? errorMessage,
    bool clearError = false,
    String? successMessage,
    bool clearSuccess = false,
    List<ZeepubVolume>? volumes,
    int? totalVolumes,
    int? currentPage,
    int? totalPages,
    String? searchQuery,
    String? selectedSeriesId,
    bool clearSeriesFilter = false,
    int? selectedWorkgroupId,
    bool clearWorkgroupFilter = false,
    String? selectedColorMode,
    bool clearColorFilter = false,
    bool? filterUncensored,
    bool clearUncensoredFilter = false,
    List<ZeepubSeries>? seriesList,
    int? totalSeries,
    List<ZeepubWorkgroup>? workgroups,
    List<ZeepubChannel>? channels,
    List<ZeepubTemplate>? templates,
    List<ZeepubQueueItem>? queue,
    List<ZeepubPostItem>? posts,
    ZeepubVolume? activeVolume,
    bool clearActiveVolume = false,
    ZeepubVolume? publishingVolume,
    bool clearPublishingVolume = false,
    ZeepubAiSuggestion? latestAiSuggestion,
    bool clearAiSuggestion = false,
    String? baseUrl,
  }) {
    return ZeepubEditorialState(
      loading: loading ?? this.loading,
      saving: saving ?? this.saving,
      aiLoading: aiLoading ?? this.aiLoading,
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
      successMessage: clearSuccess ? null : (successMessage ?? this.successMessage),
      volumes: volumes ?? this.volumes,
      totalVolumes: totalVolumes ?? this.totalVolumes,
      currentPage: currentPage ?? this.currentPage,
      totalPages: totalPages ?? this.totalPages,
      searchQuery: searchQuery ?? this.searchQuery,
      selectedSeriesId: clearSeriesFilter ? null : (selectedSeriesId ?? this.selectedSeriesId),
      selectedWorkgroupId: clearWorkgroupFilter ? null : (selectedWorkgroupId ?? this.selectedWorkgroupId),
      selectedColorMode: clearColorFilter ? null : (selectedColorMode ?? this.selectedColorMode),
      filterUncensored: clearUncensoredFilter ? null : (filterUncensored ?? this.filterUncensored),
      seriesList: seriesList ?? this.seriesList,
      totalSeries: totalSeries ?? this.totalSeries,
      workgroups: workgroups ?? this.workgroups,
      channels: channels ?? this.channels,
      templates: templates ?? this.templates,
      queue: queue ?? this.queue,
      posts: posts ?? this.posts,
      activeVolume: clearActiveVolume ? null : (activeVolume ?? this.activeVolume),
      publishingVolume: clearPublishingVolume ? null : (publishingVolume ?? this.publishingVolume),
      latestAiSuggestion: clearAiSuggestion ? null : (latestAiSuggestion ?? this.latestAiSuggestion),
      baseUrl: baseUrl ?? this.baseUrl,
    );
  }
}
'''

# 4. Cubit
cubit_code = r'''import 'package:flutter_bloc/flutter_bloc.dart';

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
      final seriesRes = await _repo.getSeriesList(page: 1, pageSize: 100);
      final volumesRes = await _repo.getVolumes(page: 1, pageSize: 30);
      final channels = await _repo.getChannels();
      final templates = await _repo.getTemplates();
      final queue = await _repo.getQueue();
      final posts = await _repo.getPostsHistory();

      emit(state.copyWith(
        loading: false,
        workgroups: workgroups,
        seriesList: seriesRes.items,
        totalSeries: seriesRes.total,
        volumes: volumesRes.items,
        totalVolumes: volumesRes.total,
        totalPages: volumesRes.totalPages,
        currentPage: 1,
        channels: channels,
        templates: templates,
        queue: queue,
        posts: posts,
      ));
    } catch (e) {
      emit(state.copyWith(
        loading: false,
        errorMessage: 'Error al conectar con ZeePub: $e',
      ));
    }
  }

  Future<void> updateBaseUrl(String url) async {
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
        pageSize: 30,
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
'''

with open(os.path.join(datasources_dir, "zeepub_api_client.dart"), "w", encoding="utf-8") as f:
    f.write(api_client_code)
with open(os.path.join(repositories_dir, "zeepub_editorial_repository.dart"), "w", encoding="utf-8") as f:
    f.write(repository_code)
with open(os.path.join(cubit_dir, "zeepub_editorial_state.dart"), "w", encoding="utf-8") as f:
    f.write(state_code)
with open(os.path.join(cubit_dir, "zeepub_editorial_cubit.dart"), "w", encoding="utf-8") as f:
    f.write(cubit_code)

print("Updated ApiClient, Repository, State and Cubit successfully")
