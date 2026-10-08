import os

client_path = r'E:\Descargas\ZeeTools\lib\features\zeepub_editorial\data\datasources\zeepub_api_client.dart'
with open(client_path, 'r', encoding='utf-8') as f:
    ccode = f.read()

old_get_series_grid = """  // --- Series Catalog ---
  Future<({List<ZeepubSeries> items, int total, int page, int totalPages})> getSeriesGrid({
    String? query,
    String? category,
    String? sortBy,
    int page = 1,
    int limit = 24,
  }) async {
    final params = <String, String>{
      'page': page.toString(),
      'limit': limit.toString(),
    };
    if (query != null && query.isNotEmpty) params['query'] = query;
    if (sortBy != null && sortBy.isNotEmpty) params['sort_by'] = sortBy;
    if (category != null && category.isNotEmpty && category != 'all') {
      if (['Novela Ligera', 'Manga', 'Web Novel'].contains(category)) {
        params['book_type'] = category;
      } else {
        params['demography'] = category;
      }
    }

    try {
      final res = await _get('/api/editorial/series/grid', params);
      final itemsJson = res['series'] as List? ?? [];
      final items = itemsJson.map((e) => ZeepubSeries.fromJson(e as Map<String, dynamic>)).toList();
      final total = (res['total'] as num?)?.toInt() ?? items.length;
      final totalPages = (res['total_pages'] as num?)?.toInt() ?? ((total + limit - 1) ~/ limit);
      return (items: items, total: total, page: page, totalPages: totalPages > 0 ? totalPages : 1);
    } catch (_) {
      try {
        final rpcData = <String, dynamic>{
          'query': query ?? '',
          'page': page,
          'limit': limit,
          'sort_by': sortBy ?? 'name_asc',
        };
        if (category != null && category.isNotEmpty && category != 'all') {
          if (['Novela Ligera', 'Manga', 'Web Novel'].contains(category)) {
            rpcData['book_type'] = category;
          } else {
            rpcData['demography'] = category;
          }
        }

        final res = await _post('/api/bot', {
          'action': 'admin_get_library_grid',
          'data': rpcData,
        });
        final itemsJson = (res['series'] ?? res['items'] ?? []) as List;
        final items = itemsJson.map((e) => ZeepubSeries.fromJson(e as Map<String, dynamic>)).toList();
        final total = (res['total'] as num?)?.toInt() ?? items.length;
        final totalPages = (total + limit - 1) ~/ limit;
        return (items: items, total: total, page: page, totalPages: totalPages > 0 ? totalPages : 1);
      } catch (_) {
        return (items: <ZeepubSeries>[], total: 0, page: page, totalPages: 1);
      }
    }
  }"""

new_get_series_grid = """  // --- Series Catalog ---
  Future<({List<ZeepubSeries> items, int total, int page, int totalPages})> getSeriesGrid({
    String? query,
    String? category,
    String? sortBy,
    int page = 1,
    int limit = 24,
  }) async {
    // 1. Try /api/editorial/series/grid
    try {
      final params = <String, String>{
        'page': page.toString(),
        'limit': limit.toString(),
      };
      if (query != null && query.isNotEmpty) params['query'] = query;
      if (sortBy != null && sortBy.isNotEmpty) params['sort_by'] = sortBy;
      if (category != null && category.isNotEmpty && category != 'all') {
        if (['Novela Ligera', 'Manga', 'Web Novel'].contains(category)) {
          params['book_type'] = category;
        } else {
          params['demography'] = category;
        }
      }
      final res = await _get('/api/editorial/series/grid', params);
      final itemsJson = (res['series'] ?? res['results'] ?? res['items'] ?? []) as List;
      if (itemsJson.isNotEmpty) {
        final items = itemsJson.map((e) => ZeepubSeries.fromJson(Map<String, dynamic>.from(e as Map))).toList();
        final total = (res['total'] as num?)?.toInt() ?? (res['total_series'] as num?)?.toInt() ?? items.length;
        final totalPages = (res['total_pages'] as num?)?.toInt() ?? ((total + limit - 1) ~/ limit);
        return (items: items, total: total, page: page, totalPages: totalPages > 0 ? totalPages : 1);
      }
    } catch (_) {}

    // 2. Try /api/editorial/series
    try {
      final res = await _get('/api/editorial/series', {
        'page': page.toString(),
        'page_size': limit.toString(),
        if (query != null && query.isNotEmpty) 'query': query,
      });
      final itemsJson = (res['items'] ?? res['series'] ?? []) as List;
      if (itemsJson.isNotEmpty) {
        final items = itemsJson.map((e) => ZeepubSeries.fromJson(Map<String, dynamic>.from(e as Map))).toList();
        final total = (res['total'] as num?)?.toInt() ?? items.length;
        final totalPages = (res['total_pages'] as num?)?.toInt() ?? ((total + limit - 1) ~/ limit);
        return (items: items, total: total, page: page, totalPages: totalPages > 0 ? totalPages : 1);
      }
    } catch (_) {}

    // 3. Try RPC action: admin_get_library_grid
    try {
      final rpcData = <String, dynamic>{
        'query': query ?? '',
        'page': page,
        'limit': limit,
        'sort_by': sortBy ?? 'name_asc',
      };
      if (category != null && category.isNotEmpty && category != 'all') {
        if (['Novela Ligera', 'Manga', 'Web Novel'].contains(category)) {
          rpcData['book_type'] = category;
        } else {
          rpcData['demography'] = category;
        }
      }

      final res = await _post('/api/bot', {
        'action': 'admin_get_library_grid',
        'data': rpcData,
      });
      final itemsJson = (res['series'] ?? res['results'] ?? res['items'] ?? []) as List;
      if (itemsJson.isNotEmpty) {
        final items = itemsJson.map((e) => ZeepubSeries.fromJson(Map<String, dynamic>.from(e as Map))).toList();
        final total = (res['total'] as num?)?.toInt() ?? (res['total_series'] as num?)?.toInt() ?? (res['totalItems'] as num?)?.toInt() ?? items.length;
        final totalPages = (res['total_pages'] as num?)?.toInt() ?? (res['pages'] as num?)?.toInt() ?? ((total + limit - 1) ~/ limit);
        return (items: items, total: total, page: page, totalPages: totalPages > 0 ? totalPages : 1);
      }
    } catch (_) {}

    // 4. Try RPC action: search (universal series search fallback on VPS)
    try {
      final res = await _post('/api/bot', {
        'action': 'search',
        'data': {
          'query': query ?? '',
          'page': page,
          'type': (category != null && category != 'all') ? category : 'todos',
          'sort': sortBy == 'name_desc' ? 'z-a' : 'a-z',
        },
      });
      final itemsJson = (res['results'] ?? res['series'] ?? res['items'] ?? []) as List;
      if (itemsJson.isNotEmpty) {
        final items = itemsJson.map((e) => ZeepubSeries.fromJson(Map<String, dynamic>.from(e as Map))).toList();
        final total = (res['totalItems'] as num?)?.toInt() ?? (res['total'] as num?)?.toInt() ?? items.length;
        final totalPages = (res['totalPages'] as num?)?.toInt() ?? ((total + limit - 1) ~/ limit);
        return (items: items, total: total, page: page, totalPages: totalPages > 0 ? totalPages : 1);
      }
    } catch (_) {}

    // 5. Fallback: Group series from loaded volumes if series endpoints failed
    try {
      final volRes = await getVolumes(page: 1, pageSize: 100, query: query);
      final seriesMap = <String, ZeepubSeries>{};
      for (final v in volRes.items) {
        final sId = v.seriesId ?? v.seriesName ?? v.title;
        if (!seriesMap.containsKey(sId)) {
          seriesMap[sId] = ZeepubSeries(
            id: sId,
            seriesHash: sId,
            name: v.seriesName?.isNotEmpty == true ? v.seriesName! : v.title,
            seriesEnglish: v.seriesName?.isNotEmpty == true ? v.seriesName! : v.englishTitle,
            seriesSpanish: v.seriesSpanish ?? v.spanishTitle,
            author: v.author ?? '',
            illustrator: v.illustrator ?? '',
            publisher: v.publisher ?? '',
            bookCount: 1,
            coverUrl: v.coverUrl ?? '',
            books: [v],
          );
        } else {
          final existing = seriesMap[sId]!;
          seriesMap[sId] = existing.copyWith(
            bookCount: existing.bookCount + 1,
            books: [...existing.books, v],
          );
        }
      }
      final grouped = seriesMap.values.toList();
      return (items: grouped, total: grouped.length, page: 1, totalPages: 1);
    } catch (_) {}

    return (items: <ZeepubSeries>[], total: 0, page: page, totalPages: 1);
  }"""

if old_get_series_grid in ccode:
    ccode = ccode.replace(old_get_series_grid, new_get_series_grid)
    with open(client_path, 'w', encoding='utf-8') as f:
        f.write(ccode)
    print("Updated getSeriesGrid with 5-tier fallback!")
else:
    print("Could not find exact block to replace, writing full client...")
