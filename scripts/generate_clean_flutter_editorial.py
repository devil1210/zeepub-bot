# -*- coding: utf-8 -*-
import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Wrote {path}")

# =========================================================================
# 1. inject_dependencies.dart
# =========================================================================
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
  getIt.registerLazySingleton<ZeepubEditorialRepository>(() => ZeepubEditorialRepository(apiClient: getIt(), prefsRepo: getIt()));

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

# =========================================================================
# 2. zeepub_workgroup.dart
# =========================================================================
write_file(r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\data\models\zeepub_workgroup.dart", """class ZeepubWorkgroup {
  final int id;
  final String name;
  final String siglas;
  final String url;
  final String description;

  const ZeepubWorkgroup({
    required this.id,
    required this.name,
    this.siglas = '',
    this.url = '',
    this.description = '',
  });

  factory ZeepubWorkgroup.fromJson(Map<String, dynamic> json) {
    return ZeepubWorkgroup(
      id: json['id'] is int ? json['id'] as int : int.tryParse(json['id'].toString()) ?? 0,
      name: (json['name'] ?? '').toString(),
      siglas: (json['siglas'] ?? '').toString(),
      url: (json['url'] ?? json['website_url'] ?? '').toString(),
      description: (json['description'] ?? '').toString(),
    );
  }

  String get displayName => siglas.isNotEmpty ? '$name ($siglas)' : name;
  String get websiteUrl => url;
}
""")

# =========================================================================
# 3. volume_edit_dialog.dart
# =========================================================================
write_file(r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\views\widgets\volume_edit_dialog.dart", """import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '/features/zeepub_editorial/data/models/zeepub_volume.dart';
import '/features/zeepub_editorial/presentation/cubit/zeepub_editorial_cubit.dart';
import '/features/zeepub_editorial/presentation/cubit/zeepub_editorial_state.dart';

class VolumeEditDialog extends StatefulWidget {
  final ZeepubVolume volume;
  final String baseUrl;

  const VolumeEditDialog({
    super.key,
    required this.volume,
    required this.baseUrl,
  });

  @override
  State<VolumeEditDialog> createState() => _VolumeEditDialogState();
}

class _VolumeEditDialogState extends State<VolumeEditDialog> {
  late TextEditingController _titleController;
  late TextEditingController _spanishTitleController;
  late TextEditingController _englishTitleController;
  late TextEditingController _volumeController;
  late TextEditingController _editionController;
  late TextEditingController _authorController;
  late TextEditingController _illustratorController;
  late TextEditingController _translatorController;
  late TextEditingController _layoutByController;
  late TextEditingController _publisherController;
  late TextEditingController _descriptionController;

  String _colorMode = 'mono';
  bool _isUncensored = false;

  @override
  void initState() {
    super.initState();
    final v = widget.volume;
    _titleController = TextEditingController(text: v.title);
    _spanishTitleController = TextEditingController(text: v.spanishTitle);
    _englishTitleController = TextEditingController(text: v.englishTitle);
    _volumeController = TextEditingController(
      text: v.volume != null ? (v.volume! % 1 == 0 ? v.volume!.toInt().toString() : v.volume!.toString()) : '',
    );
    _editionController = TextEditingController(text: v.edition ?? '');
    _authorController = TextEditingController(text: v.author ?? '');
    _illustratorController = TextEditingController(text: v.illustrator ?? '');
    _translatorController = TextEditingController(text: v.translator ?? '');
    _layoutByController = TextEditingController(text: v.layoutBy ?? '');
    _publisherController = TextEditingController(text: v.publisher ?? '');
    _descriptionController = TextEditingController(text: v.description ?? '');

    _colorMode = v.colorMode ?? 'mono';
    _isUncensored = v.isUncensored;
  }

  @override
  void dispose() {
    _titleController.dispose();
    _spanishTitleController.dispose();
    _englishTitleController.dispose();
    _volumeController.dispose();
    _editionController.dispose();
    _authorController.dispose();
    _illustratorController.dispose();
    _translatorController.dispose();
    _layoutByController.dispose();
    _publisherController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  void _applyAiSuggestion(ZeepubEditorialState state) {
    final s = state.latestAiSuggestion;
    if (s == null) return;
    setState(() {
      if (s.seriesSpanish.isNotEmpty) _spanishTitleController.text = s.seriesSpanish;
      if (s.volume != null) {
        _volumeController.text = s.volume! % 1 == 0 ? s.volume!.toInt().toString() : s.volume!.toString();
      }
      if (s.author.isNotEmpty) _authorController.text = s.author;
      if (s.illustrator.isNotEmpty) _illustratorController.text = s.illustrator;
      if (s.publisher.isNotEmpty) _publisherController.text = s.publisher;
    });
  }

  String _buildCoverUrl() {
    if (widget.volume.coverUrl == null || widget.volume.coverUrl!.isEmpty) return '';
    if (widget.volume.coverUrl!.startsWith('http')) return widget.volume.coverUrl!;
    final cleanBase = widget.baseUrl.replaceAll(RegExp(r"/+$"), "");
    final cleanPath = widget.volume.coverUrl!.startsWith('/') ? widget.volume.coverUrl! : '/${widget.volume.coverUrl!}';
    return '$cleanBase$cleanPath';
  }

  Future<void> _handleSave() async {
    final cubit = context.read<ZeepubEditorialCubit>();
    final volNum = double.tryParse(_volumeController.text.trim());

    final payload = <String, dynamic>{
      'title': _titleController.text.trim(),
      'spanish_title': _spanishTitleController.text.trim(),
      'english_title': _englishTitleController.text.trim(),
      'volume': volNum,
      'edition': _editionController.text.trim(),
      'color_mode': _colorMode,
      'is_uncensored': _isUncensored,
      'author': _authorController.text.trim(),
      'illustrator': _illustratorController.text.trim(),
      'translator': _translatorController.text.trim(),
      'layout_by': _layoutByController.text.trim(),
      'publisher': _publisherController.text.trim(),
      'description': _descriptionController.text.trim(),
    };

    await cubit.saveVolume(widget.volume.bookHash, payload);
    if (mounted) {
      Navigator.of(context).pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final tt = Theme.of(context).textTheme;
    final coverUrl = _buildCoverUrl();

    return BlocConsumer<ZeepubEditorialCubit, ZeepubEditorialState>(
      listener: (context, state) {
        if (state.latestAiSuggestion != null) {
          _applyAiSuggestion(state);
        }
      },
      builder: (context, state) {
        final cubit = context.read<ZeepubEditorialCubit>();

        return Dialog(
          insetPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 860, maxHeight: 720),
            child: Padding(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Header
                  Row(
                    children: [
                      Icon(Icons.edit_note_rounded, size: 28, color: cs.primary),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Editar Metadatos del Tomo',
                              style: tt.titleLarge?.copyWith(fontWeight: FontWeight.bold),
                            ),
                            Text(
                              widget.volume.filename ?? widget.volume.bookHash,
                              style: tt.bodySmall?.copyWith(color: cs.onSurfaceVariant),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ],
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close),
                        onPressed: () => Navigator.of(context).pop(),
                      ),
                    ],
                  ),
                  const Divider(height: 24),

                  // Body Content
                  Expanded(
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Left Column: Cover & AI Suggestion
                        SizedBox(
                          width: 180,
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              ClipRRect(
                                borderRadius: BorderRadius.circular(8),
                                child: AspectRatio(
                                  aspectRatio: 0.7,
                                  child: coverUrl.isNotEmpty
                                      ? Image.network(
                                          coverUrl,
                                          fit: BoxFit.cover,
                                          errorBuilder: (_, __, ___) => Container(
                                            color: cs.surfaceContainerHighest,
                                            child: const Icon(Icons.broken_image_rounded, size: 36),
                                          ),
                                        )
                                      : Container(
                                          color: cs.surfaceContainerHighest,
                                          child: const Icon(Icons.book, size: 36),
                                        ),
                                ),
                              ),
                              const SizedBox(height: 16),
                              FilledButton.tonalIcon(
                                icon: state.aiLoading
                                    ? const SizedBox(
                                        width: 16,
                                        height: 16,
                                        child: CircularProgressIndicator(strokeWidth: 2),
                                      )
                                    : const Icon(Icons.auto_awesome, size: 16),
                                label: const Text('Completar con IA'),
                                onPressed: state.aiLoading
                                    ? null
                                    : () => cubit.requestAiSuggestion(_titleController.text.isNotEmpty ? _titleController.text : widget.volume.title),
                              ),
                              const SizedBox(height: 8),
                              OutlinedButton.icon(
                                icon: const Icon(Icons.sync_rounded, size: 16),
                                label: const Text('Re-escanear EPUB'),
                                onPressed: state.saving
                                    ? null
                                    : () => cubit.syncVolumeFromDisk(widget.volume.bookHash),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 24),

                        // Right Column: Form Fields
                        Expanded(
                          child: SingleChildScrollView(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.stretch,
                              children: [
                                // Title Fields
                                TextFormField(
                                  controller: _titleController,
                                  decoration: const InputDecoration(
                                    labelText: 'Título Original / Romaji (EPUB)',
                                    border: OutlineInputBorder(),
                                    isDense: true,
                                  ),
                                ),
                                const SizedBox(height: 12),
                                TextFormField(
                                  controller: _spanishTitleController,
                                  decoration: const InputDecoration(
                                    labelText: 'Título en Español (Oficial / Fansub)',
                                    border: OutlineInputBorder(),
                                    isDense: true,
                                  ),
                                ),
                                const SizedBox(height: 12),
                                TextFormField(
                                  controller: _englishTitleController,
                                  decoration: const InputDecoration(
                                    labelText: 'Título en Inglés (Referencia)',
                                    border: OutlineInputBorder(),
                                    isDense: true,
                                  ),
                                ),
                                const SizedBox(height: 16),

                                // Volume & Edition Row
                                Row(
                                  children: [
                                    Expanded(
                                      child: TextFormField(
                                        controller: _volumeController,
                                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                                        decoration: const InputDecoration(
                                          labelText: 'Número de Tomo (ej. 1, 1.5, 2)',
                                          border: OutlineInputBorder(),
                                          isDense: true,
                                        ),
                                      ),
                                    ),
                                    const SizedBox(width: 12),
                                    Expanded(
                                      child: TextFormField(
                                        controller: _editionController,
                                        decoration: const InputDecoration(
                                          labelText: 'Edición / Especial (ej. Especial, SS)',
                                          border: OutlineInputBorder(),
                                          isDense: true,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 16),

                                // Badges: Color Mode & Uncensored
                                Row(
                                  children: [
                                    Expanded(
                                      child: DropdownButtonFormField<String>(
                                        initialValue: _colorMode,
                                        decoration: const InputDecoration(
                                          labelText: 'Modo de Color',
                                          border: OutlineInputBorder(),
                                          isDense: true,
                                        ),
                                        items: const [
                                          DropdownMenuItem(value: 'mono', child: Text('Monocromo (B/N)')),
                                          DropdownMenuItem(value: 'color', child: Text('Ilustraciones a Color')),
                                        ],
                                        onChanged: (val) {
                                          if (val != null) setState(() => _colorMode = val);
                                        },
                                      ),
                                    ),
                                    const SizedBox(width: 16),
                                    Expanded(
                                      child: CheckboxListTile(
                                        value: _isUncensored,
                                        title: const Text('Sin Censura / +18'),
                                        dense: true,
                                        contentPadding: EdgeInsets.zero,
                                        controlAffinity: ListTileControlAffinity.leading,
                                        onChanged: (val) {
                                          setState(() => _isUncensored = val ?? false);
                                        },
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 16),

                                // Creators Row 1
                                Row(
                                  children: [
                                    Expanded(
                                      child: TextFormField(
                                        controller: _authorController,
                                        decoration: const InputDecoration(
                                          labelText: 'Autor',
                                          border: OutlineInputBorder(),
                                          isDense: true,
                                        ),
                                      ),
                                    ),
                                    const SizedBox(width: 12),
                                    Expanded(
                                      child: TextFormField(
                                        controller: _illustratorController,
                                        decoration: const InputDecoration(
                                          labelText: 'Ilustrador',
                                          border: OutlineInputBorder(),
                                          isDense: true,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 12),

                                // Creators Row 2
                                Row(
                                  children: [
                                    Expanded(
                                      child: TextFormField(
                                        controller: _translatorController,
                                        decoration: const InputDecoration(
                                          labelText: 'Traductor',
                                          border: OutlineInputBorder(),
                                          isDense: true,
                                        ),
                                      ),
                                    ),
                                    const SizedBox(width: 12),
                                    Expanded(
                                      child: TextFormField(
                                        controller: _layoutByController,
                                        decoration: const InputDecoration(
                                          labelText: 'Maquetador / Diseño',
                                          border: OutlineInputBorder(),
                                          isDense: true,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 12),

                                // Publisher / Fansub
                                TextFormField(
                                  controller: _publisherController,
                                  decoration: const InputDecoration(
                                    labelText: 'Fansub / Grupo / Editorial',
                                    border: OutlineInputBorder(),
                                    isDense: true,
                                  ),
                                ),
                                const SizedBox(height: 12),

                                // Description / Synopsis
                                TextFormField(
                                  controller: _descriptionController,
                                  maxLines: 4,
                                  decoration: const InputDecoration(
                                    labelText: 'Sinopsis / Descripción',
                                    border: OutlineInputBorder(),
                                    alignLabelWithHint: true,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const Divider(height: 24),

                  // Actions
                  Row(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      TextButton(
                        onPressed: () => Navigator.of(context).pop(),
                        child: const Text('Cancelar'),
                      ),
                      const SizedBox(width: 12),
                      FilledButton.icon(
                        icon: state.saving
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                              )
                            : const Icon(Icons.save_rounded),
                        label: const Text('Guardar Metadatos'),
                        onPressed: state.saving ? null : _handleSave,
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

# =========================================================================
# 4. telegram_simulator.dart
# =========================================================================
write_file(r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\views\widgets\telegram_simulator.dart", """import 'package:flutter/material.dart';

import '/features/zeepub_editorial/data/models/zeepub_channel.dart';
import '/features/zeepub_editorial/data/models/zeepub_series.dart';
import '/features/zeepub_editorial/data/models/zeepub_volume.dart';

class TelegramSimulator extends StatefulWidget {
  final String templateContent;
  final ZeepubVolume? volume;
  final ZeepubSeries? series;
  final ZeepubChannel? channel;
  final String? customCoverUrl;
  final bool sendAsFile;

  const TelegramSimulator({
    super.key,
    required this.templateContent,
    this.volume,
    this.series,
    this.channel,
    this.customCoverUrl,
    this.sendAsFile = true,
  });

  @override
  State<TelegramSimulator> createState() => _TelegramSimulatorState();
}

class _TelegramSimulatorState extends State<TelegramSimulator> {
  bool _showFicha = true;
  bool _showSinopsis = false;

  String _formatGenres(String? raw) {
    if (raw == null || raw.trim().isEmpty) return '#NovelaLigera #Fantasia';
    final parts = raw.split(RegExp(r'[,;|]')).map((s) => s.trim()).where((s) => s.isNotEmpty);
    return parts.map((g) {
      final clean = g.replaceAll('#', '').trim().replaceAll(' ', '_');
      return '#$clean';
    }).join(' ');
  }

  String _interpolate(String tpl) {
    final v = widget.volume;
    final s = widget.series;

    final serieEng = (v?.englishTitle.isNotEmpty == true)
        ? v!.englishTitle
        : ((s != null && s.seriesEnglish.isNotEmpty) ? s.seriesEnglish : (s?.name ?? 'The Hidden Dungeon Only I Can Enter'));
    final serieSpa = (v?.spanishTitle.isNotEmpty == true)
        ? v!.spanishTitle
        : ((s != null && s.seriesSpanish.isNotEmpty) ? s.seriesSpanish : 'El calabozo oculto en el que solo yo puedo entrar');
    final serieRom = (s != null && s.name.isNotEmpty) ? s.name : 'Ore dake Haireru Kakushi Dungeon';
    final volNum = v?.volume != null ? (v!.volume! % 1 == 0 ? v.volume!.toInt().toString() : v.volume!.toString()) : '1.0';
    final autor = (v?.author != null && v!.author!.isNotEmpty) ? v.author! : ((s != null && s.author.isNotEmpty) ? s.author : 'Meguru Seto');
    final ilustrador = (v?.illustrator != null && v!.illustrator!.isNotEmpty) ? v.illustrator! : ((s != null && s.illustrator.isNotEmpty) ? s.illustrator : 'Note Takehana');
    final traductor = (v?.translator != null && v!.translator!.isNotEmpty) ? v.translator! : 'Hitsugaya Rin';
    final layoutBy = (v?.layoutBy != null && v!.layoutBy!.isNotEmpty) ? v.layoutBy! : 'ZeePubs';
    final editorial = (v?.publisher != null && v!.publisher!.isNotEmpty) ? v.publisher! : ((s != null && s.publisher.isNotEmpty) ? s.publisher : "God's Earth Translations");
    final sinopsis = (v?.description != null && v!.description!.isNotEmpty)
        ? v.description!
        : ((s?.description != null && s!.description!.isNotEmpty)
            ? s.description!
            : 'Noir, el tercer hijo de un "noble mendigo", perdió su trabajo y el rumbo de su vida, pero la fortuna golpeó justo cuando estaba contemplando convertirse en aventurero...');
    final demography = v?.colorMode == 'color' ? 'Shounen' : 'Seinen';
    final genres = _formatGenres('#Romance #Sobrenatural #Comedia #Ecchi #Accion #Aventura #Fantasia');
    final slug = (s != null && s.slug.isNotEmpty) ? s.slug : 'Ore_Dake_Haireru_Kakushi_Dungeon';
    final fecha = DateTime.now().toString().split(' ')[0];

    final values = <String, String>{
      'serie': serieEng,
      'series': serieEng,
      'series_english': serieEng,
      'series_spanish': serieSpa,
      'romaji_title': serieRom,
      'titulo': serieSpa,
      'title': serieEng,
      'volumen': volNum,
      'volume': volNum,
      'autor': autor,
      'author': autor,
      'illustrator': ilustrador,
      'ilustrador': ilustrador,
      'traductor': traductor,
      'translator': traductor,
      'layout_by': layoutBy,
      'maquetador': layoutBy,
      'editorial': editorial,
      'publisher': editorial,
      'sinopsis': sinopsis,
      'synopsis': sinopsis,
      'demography': demography,
      'genres': genres,
      'slug': slug,
      'fecha': fecha,
      'published_at': fecha,
      'download_link': 'https://t.me/zeepub_bot?start=book_123',
    };

    var result = tpl;

    // Handle conditionals [?key]...[/?] and {?key}...{/?}
    result = result.replaceAllMapped(RegExp(r'\\[\\?([a-zA-Z0-9_]+)\\](.*?)\\[/\\?\\]', dotAll: true), (m) {
      final key = m.group(1)!;
      final content = m.group(2)!;
      final val = values[key] ?? '';
      return val.trim().isNotEmpty ? content : '';
    });

    result = result.replaceAllMapped(RegExp(r'\\{\\?([a-zA-Z0-9_]+)\\}(.*?)\\{/\\?\\}', dotAll: true), (m) {
      final key = m.group(1)!;
      final content = m.group(2)!;
      final val = values[key] ?? '';
      return val.trim().isNotEmpty ? content : '';
    });

    // Replace variables
    for (final entry in values.entries) {
      result = result.replaceAll('{${entry.key}}', entry.value);
    }

    return result;
  }

  @override
  Widget build(BuildContext context) {
    const defaultTpl = '{?series_english}<b>[EN] {series_english}</b>{/?}\\n'
        '{?romaji_title}<b>[JA] {romaji_title}</b>{/?}\\n'
        '{?series_spanish}<b>[ES] {series_spanish}</b>{/?}\\n'
        '<b>Volumen {volumen}</b>\\n'
        '{genres}\\n\\n'
        'Ficha Tecnica:\\n'
        '• Autor: {autor}\\n'
        '• Ilustrador: {illustrator}\\n'
        '• Traductor: {traductor}\\n'
        '• Editorial: {editorial}\\n\\n'
        'Sinopsis:\\n{sinopsis}\\n\\n'
        '#{slug}';

    final tpl = widget.templateContent.trim().isNotEmpty ? widget.templateContent : defaultTpl;
    final evaluatedRaw = _interpolate(tpl);
    final charCount = evaluatedRaw.length;
    final channelName = widget.channel != null && widget.channel!.name.isNotEmpty ? widget.channel!.name : 'Canal Oficial ZeePub';
    final v = widget.volume;
    final s = widget.series;
    final coverUrl = widget.customCoverUrl ?? v?.coverUrl ?? s?.coverUrl ?? '';

    final serieEng = (v?.englishTitle.isNotEmpty == true)
        ? v!.englishTitle
        : ((s != null && s.seriesEnglish.isNotEmpty) ? s.seriesEnglish : (s?.name ?? 'The Hidden Dungeon Only I Can Enter'));
    final serieSpa = (v?.spanishTitle.isNotEmpty == true)
        ? v!.spanishTitle
        : ((s != null && s.seriesSpanish.isNotEmpty) ? s.seriesSpanish : 'El calabozo oculto en el que solo yo puedo entrar');
    final serieRom = (s != null && s.name.isNotEmpty) ? s.name : 'Ore dake Haireru Kakushi Dungeon';
    final volNum = v?.volume != null ? (v!.volume! % 1 == 0 ? v.volume!.toInt().toString() : v.volume!.toString()) : '1';
    final autor = (v?.author != null && v!.author!.isNotEmpty) ? v.author! : ((s != null && s.author.isNotEmpty) ? s.author : 'Meguru Seto');
    final ilustrador = (v?.illustrator != null && v!.illustrator!.isNotEmpty) ? v.illustrator! : ((s != null && s.illustrator.isNotEmpty) ? s.illustrator : 'Note Takehana');
    final traductor = (v?.translator != null && v!.translator!.isNotEmpty) ? v.translator! : 'Hitsugaya Rin';
    final editorial = (v?.publisher != null && v!.publisher!.isNotEmpty) ? v.publisher! : ((s != null && s.publisher.isNotEmpty) ? s.publisher : "God's Earth Translations");
    final sinopsis = (v?.description != null && v!.description!.isNotEmpty)
        ? v.description!
        : ((s?.description != null && s!.description!.isNotEmpty)
            ? s.description!
            : 'Noir, el tercer hijo de un "noble mendigo", perdió su trabajo y el rumbo de su vida...');
    final genres = _formatGenres('#Romance #Sobrenatural #Comedia #Ecchi #Accion #Aventura #Fantasia');
    final slug = (s != null && s.slug.isNotEmpty) ? s.slug : 'Ore_Dake_Haireru_Kakushi_Dungeon';

    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // SIMULATOR HEADER
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: const Color(0xFF1E293B),
              borderRadius: const BorderRadius.vertical(top: Radius.circular(15)),
              border: Border(bottom: BorderSide(color: Colors.white.withValues(alpha: 0.05))),
            ),
            child: Row(
              children: [
                const Icon(Icons.send_rounded, size: 16, color: Color(0xFF38BDF8)),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'SIMULADOR OFICIAL DE CANAL (DESKTOP)',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 0.5,
                      color: Colors.grey.shade400,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: charCount > 4096 ? Colors.red.withValues(alpha: 0.2) : Colors.blue.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: charCount > 4096 ? Colors.red : Colors.blue.shade700),
                  ),
                  child: Text(
                    '$charCount / 4096 caracteres',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: charCount > 4096 ? Colors.redAccent : const Color(0xFF38BDF8),
                    ),
                  ),
                ),
              ],
            ),
          ),

          // TELEGRAM DESKTOP CHANNEL VIEW
          Expanded(
            child: Container(
              color: const Color(0xFF0E1621),
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  // Channel Header Bar
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: const Color(0xFF17212B),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      children: [
                        CircleAvatar(
                          radius: 14,
                          backgroundColor: Colors.blue.shade600,
                          child: const Icon(Icons.auto_stories, size: 14, color: Colors.white),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                channelName,
                                style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                              const Text(
                                'canal de difusión',
                                style: TextStyle(color: Color(0xFF708499), fontSize: 11),
                              ),
                            ],
                          ),
                        ),
                        const Icon(Icons.volume_off_rounded, size: 16, color: Color(0xFF708499)),
                      ],
                    ),
                  ),
                  const SizedBox(height: 12),

                  // TELEGRAM MESSAGE CARD
                  Align(
                    alignment: Alignment.centerLeft,
                    child: Container(
                      constraints: const BoxConstraints(maxWidth: 420),
                      decoration: BoxDecoration(
                        color: const Color(0xFF182533),
                        borderRadius: BorderRadius.circular(12),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withValues(alpha: 0.4),
                            blurRadius: 8,
                            offset: const Offset(0, 2),
                          ),
                        ],
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          // COVER PHOTO
                          if (coverUrl.isNotEmpty)
                            ClipRRect(
                              borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
                              child: AspectRatio(
                                aspectRatio: 1.4,
                                child: Image.network(
                                  coverUrl.startsWith('http') ? coverUrl : 'http://localhost:8001$coverUrl',
                                  fit: BoxFit.cover,
                                  errorBuilder: (_, _, _) => Container(
                                    color: const Color(0xFF242F3D),
                                    child: const Center(
                                      child: Icon(Icons.auto_stories, size: 48, color: Color(0xFF708499)),
                                    ),
                                  ),
                                ),
                              ),
                            ),

                          // MESSAGE BODY
                          Padding(
                            padding: const EdgeInsets.all(12),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                // Titles
                                Text(serieEng, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13)),
                                Text(serieRom, style: const TextStyle(color: Colors.white70, fontWeight: FontWeight.bold, fontSize: 12)),
                                Text(serieSpa, style: const TextStyle(color: Colors.white70, fontSize: 12)),
                                const SizedBox(height: 4),
                                Text('Volumen $volNum', style: const TextStyle(color: Color(0xFF53A6E7), fontWeight: FontWeight.bold, fontSize: 13)),
                                const SizedBox(height: 4),
                                Text(genres, style: const TextStyle(color: Color(0xFF53A6E7), fontSize: 12)),
                                const SizedBox(height: 8),

                                // Ficha Tecnica Accordion
                                InkWell(
                                  onTap: () => setState(() => _showFicha = !_showFicha),
                                  child: Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                                    decoration: BoxDecoration(
                                      color: const Color(0xFF242F3D),
                                      borderRadius: BorderRadius.circular(6),
                                    ),
                                    child: Row(
                                      children: [
                                        Icon(_showFicha ? Icons.arrow_drop_down : Icons.arrow_right, color: Colors.white70, size: 18),
                                        const SizedBox(width: 4),
                                        const Text('📋 Ficha Técnica', style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold)),
                                      ],
                                    ),
                                  ),
                                ),
                                if (_showFicha)
                                  Padding(
                                    padding: const EdgeInsets.fromLTRB(12, 6, 8, 8),
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        _fieldRow('Autor', autor),
                                        const SizedBox(height: 3),
                                        _fieldRow('Ilustrador', ilustrador),
                                        const SizedBox(height: 3),
                                        _fieldRow('Categoría', 'Novela Ligera'),
                                        const SizedBox(height: 3),
                                        _fieldRow('Traductor', traductor),
                                        const SizedBox(height: 3),
                                        _fieldRow('Editorial', editorial),
                                      ],
                                    ),
                                  ),

                                const SizedBox(height: 6),

                                // Sinopsis Accordion
                                InkWell(
                                  onTap: () => setState(() => _showSinopsis = !_showSinopsis),
                                  child: Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                                    decoration: BoxDecoration(
                                      color: const Color(0xFF242F3D),
                                      borderRadius: BorderRadius.circular(6),
                                    ),
                                    child: Row(
                                      children: [
                                        Icon(_showSinopsis ? Icons.arrow_drop_down : Icons.arrow_right, color: Colors.white70, size: 18),
                                        const SizedBox(width: 4),
                                        const Text('📖 Ver Sinopsis', style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold)),
                                      ],
                                    ),
                                  ),
                                ),
                                if (_showSinopsis)
                                  Container(
                                    margin: const EdgeInsets.only(top: 4, left: 4),
                                    padding: const EdgeInsets.all(8),
                                    decoration: const BoxDecoration(
                                      border: Border(left: BorderSide(color: Color(0xFF53A6E7), width: 3)),
                                      color: Color(0xFF202B36),
                                    ),
                                    child: Text(
                                      sinopsis,
                                      style: const TextStyle(color: Colors.white70, fontSize: 11, height: 1.3),
                                    ),
                                  ),

                                const SizedBox(height: 10),

                                // EPUB Document Bubble
                                if (widget.sendAsFile)
                                  Container(
                                    padding: const EdgeInsets.all(8),
                                    decoration: BoxDecoration(
                                      color: const Color(0xFF242F3D),
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: Row(
                                      children: [
                                        Container(
                                          width: 38,
                                          height: 38,
                                          decoration: const BoxDecoration(
                                            color: Color(0xFF53A6E7),
                                            shape: BoxShape.circle,
                                          ),
                                          child: const Icon(Icons.arrow_downward_rounded, color: Colors.white, size: 20),
                                        ),
                                        const SizedBox(width: 10),
                                        Expanded(
                                          child: Column(
                                            crossAxisAlignment: CrossAxisAlignment.start,
                                            children: [
                                              Text(
                                                '$serieSpa - V$volNum.epub',
                                                style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
                                                maxLines: 1,
                                                overflow: TextOverflow.ellipsis,
                                              ),
                                              const Text('3.2 MB · EPUB 3.0', style: TextStyle(color: Color(0xFF708499), fontSize: 10)),
                                            ],
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),

                                const SizedBox(height: 8),

                                // Hashtag & Timestamp
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text('#$slug', style: const TextStyle(color: Color(0xFF53A6E7), fontSize: 11)),
                                    const Row(
                                      children: [
                                        Text('12:15', style: TextStyle(color: Color(0xFF708499), fontSize: 10)),
                                        SizedBox(width: 4),
                                        Icon(Icons.done_all, size: 14, color: Color(0xFF53A6E7)),
                                      ],
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _fieldRow(String label, String value) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 80,
          child: Text(label, style: const TextStyle(color: Color(0xFF708499), fontSize: 11)),
        ),
        Expanded(
          child: Text(value, style: const TextStyle(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.w500)),
        ),
      ],
    );
  }
}
""")

# =========================================================================
# 5. templates_tab.dart
# =========================================================================
write_file(r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\views\widgets\templates_tab.dart", """import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '/features/zeepub_editorial/data/models/zeepub_template.dart';
import '/features/zeepub_editorial/presentation/cubit/zeepub_editorial_cubit.dart';
import '/features/zeepub_editorial/presentation/cubit/zeepub_editorial_state.dart';
import 'telegram_simulator.dart';

class ZeepubTemplatesTab extends StatefulWidget {
  const ZeepubTemplatesTab({super.key});

  @override
  State<ZeepubTemplatesTab> createState() => _ZeepubTemplatesTabState();
}

class _ZeepubTemplatesTabState extends State<ZeepubTemplatesTab> {
  ZeepubTemplate? _selectedTemplate;
  late final TextEditingController _nameController;
  late final TextEditingController _contentController;
  String _platform = 'telegram';
  bool _isDefault = false;

  final List<String> _variables = [
    '{serie}',
    '{volumen}',
    '{titulo}',
    '{autor}',
    '{illustrator}',
    '{traductor}',
    '{editorial}',
    '{sinopsis}',
    '{demography}',
    '{genres}',
    '{tomoid}',
    '{fecha}',
    '{published_at}',
    '{slug}',
    '{download_link}',
    '{layout_by}',
  ];

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController();
    _contentController = TextEditingController();
  }

  @override
  void dispose() {
    _nameController.dispose();
    _contentController.dispose();
    super.dispose();
  }

  void _selectTemplate(ZeepubTemplate tpl) {
    setState(() {
      _selectedTemplate = tpl;
      _nameController.text = tpl.name;
      _contentController.text = tpl.content;
      _platform = tpl.platform;
      _isDefault = tpl.isDefault;
    });
  }

  void _createNewTemplate() {
    setState(() {
      _selectedTemplate = const ZeepubTemplate(
        name: 'Nueva Plantilla Telegram',
        content: '<b>{series_english}</b>\\n[?volumen]<b>Volumen {volumen}</b>\\n[/?]#{slug}',
        platform: 'telegram',
      );
      _nameController.text = _selectedTemplate!.name;
      _contentController.text = _selectedTemplate!.content;
      _platform = 'telegram';
      _isDefault = false;
    });
  }

  void _insertTag(String tag) {
    final text = _contentController.text;
    final selection = _contentController.selection;
    final start = selection.start >= 0 ? selection.start : text.length;
    final end = selection.end >= 0 ? selection.end : text.length;
    final newText = text.replaceRange(start, end, tag);
    _contentController.value = TextEditingValue(
      text: newText,
      selection: TextSelection.collapsed(offset: start + tag.length),
    );
    setState(() {});
  }

  void _wrapTag(String open, String close) {
    final text = _contentController.text;
    final selection = _contentController.selection;
    if (selection.start >= 0 && selection.end > selection.start) {
      final selectedText = text.substring(selection.start, selection.end);
      final newText = text.replaceRange(selection.start, selection.end, '$open$selectedText$close');
      _contentController.value = TextEditingValue(
        text: newText,
        selection: TextSelection.collapsed(offset: selection.end + open.length + close.length),
      );
    } else {
      _insertTag('$open$close');
    }
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final tt = Theme.of(context).textTheme;

    return BlocBuilder<ZeepubEditorialCubit, ZeepubEditorialState>(
      builder: (context, state) {
        final cubit = context.read<ZeepubEditorialCubit>();
        final templates = state.templates;

        if (templates.isNotEmpty && _selectedTemplate == null) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            _selectTemplate(templates.first);
          });
        }

        return Row(
          children: [
            // LEFT SIDEBAR: Saved Templates List
            Container(
              width: 280,
              decoration: BoxDecoration(
                border: Border(right: BorderSide(color: cs.outlineVariant.withValues(alpha: 0.3))),
              ),
              child: Column(
                children: [
                  Padding(
                    padding: const EdgeInsets.all(12),
                    child: Row(
                      children: [
                        const Icon(Icons.folder_copy_rounded, size: 16),
                        const SizedBox(width: 8),
                        Text('PLANTILLAS GUARDADAS', style: tt.labelSmall?.copyWith(fontWeight: FontWeight.bold, letterSpacing: 0.5)),
                        const Spacer(),
                        IconButton(
                          icon: const Icon(Icons.refresh_rounded, size: 18),
                          tooltip: 'Restaurar Predeterminadas Oficiales',
                          onPressed: () => cubit.restoreTemplates(),
                        ),
                        IconButton(
                          icon: const Icon(Icons.add_rounded, size: 20),
                          tooltip: 'Nueva Plantilla',
                          onPressed: _createNewTemplate,
                        ),
                      ],
                    ),
                  ),
                  const Divider(height: 1),
                  Expanded(
                    child: ListView.builder(
                      itemCount: templates.length,
                      itemBuilder: (context, idx) {
                        final tpl = templates[idx];
                        final isSelected = _selectedTemplate?.id == tpl.id || (_selectedTemplate?.id == null && _selectedTemplate?.name == tpl.name);
                        return ListTile(
                          selected: isSelected,
                          selectedTileColor: cs.primaryContainer.withValues(alpha: 0.3),
                          leading: Icon(
                            tpl.isDefault ? Icons.star_rounded : (tpl.platform == 'facebook' ? Icons.facebook : Icons.send_rounded),
                            color: tpl.isDefault ? Colors.amber : (tpl.platform == 'facebook' ? Colors.blue : Colors.lightBlueAccent),
                            size: 20,
                          ),
                          title: Text(
                            tpl.name,
                            style: tt.bodyMedium?.copyWith(
                              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          subtitle: Text(
                            tpl.platform.toUpperCase(),
                            style: tt.labelSmall?.copyWith(color: cs.onSurfaceVariant),
                          ),
                          onTap: () => _selectTemplate(tpl),
                        );
                      },
                    ),
                  ),
                ],
              ),
            ),

            // CENTER: Template Form & Copy Editor
            Expanded(
              flex: 5,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  // Header badge
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: _isDefault ? Colors.amber.withValues(alpha: 0.2) : cs.surfaceContainerHighest,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: _isDefault ? Colors.amber : cs.outlineVariant),
                        ),
                        child: Row(
                          children: [
                            Icon(_isDefault ? Icons.star_rounded : Icons.code_rounded, size: 14, color: _isDefault ? Colors.amber : cs.onSurface),
                            const SizedBox(width: 6),
                            Text(
                              _isDefault ? 'Plantilla Oficial Predeterminada' : 'Plantilla Personalizada',
                              style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: _isDefault ? Colors.amber : cs.onSurface),
                            ),
                          ],
                        ),
                      ),
                      const Spacer(),
                      FilterChip(
                        label: const Text('Fijar Oficial'),
                        selected: _isDefault,
                        onSelected: (val) => setState(() => _isDefault = val),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),

                  Row(
                    children: [
                      Expanded(
                        flex: 3,
                        child: TextField(
                          controller: _nameController,
                          decoration: const InputDecoration(labelText: 'Nombre de la plantilla'),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        flex: 2,
                        child: DropdownButtonFormField<String>(
                          initialValue: _platform,
                          decoration: const InputDecoration(labelText: 'Plataforma objetivo'),
                          items: const [
                            DropdownMenuItem(value: 'telegram', child: Text('Telegram')),
                            DropdownMenuItem(value: 'facebook', child: Text('Facebook')),
                          ],
                          onChanged: (val) {
                            if (val != null) setState(() => _platform = val);
                          },
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // COPY EDITOR TOOLBAR
                  Text('EDITOR DE COPY', style: tt.labelLarge?.copyWith(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 6),
                  Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    children: [
                      _formatButton('B', () => _wrapTag('<b>', '</b>')),
                      _formatButton('I', () => _wrapTag('<i>', '</i>')),
                      _formatButton('U', () => _wrapTag('<u>', '</u>')),
                      _formatButton('S', () => _wrapTag('<s>', '</s>')),
                      _formatButton('Cita', () => _wrapTag('<blockquote>', '</blockquote>')),
                      _formatButton('Expandible', () => _wrapTag('<details><summary>Titulo</summary>', '</details>')),
                      _formatButton('H', () => _wrapTag('<h3>', '</h3>')),
                      _formatButton('Tabla', () => _wrapTag('<table><tr><td>', '</td></tr></table>')),
                      _formatButton('Enlace', () => _wrapTag('<a href="URL">', '</a>')),
                      _formatButton('Condicional [?]', () => _wrapTag('[?volumen]', '[/?]')),
                    ],
                  ),
                  const SizedBox(height: 12),

                  // VARIABLES DISPONIBLES
                  Text('VARIABLES DISPONIBLES (Haz clic para insertar):', style: tt.labelSmall?.copyWith(color: cs.onSurfaceVariant)),
                  const SizedBox(height: 6),
                  Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    children: [
                      for (final v in _variables)
                        ActionChip(
                          label: Text(v, style: const TextStyle(fontSize: 11, fontFamily: 'monospace')),
                          padding: EdgeInsets.zero,
                          onPressed: () => _insertTag(v),
                        ),
                    ],
                  ),
                  const SizedBox(height: 12),

                  TextField(
                    controller: _contentController,
                    maxLines: 16,
                    onChanged: (_) => setState(() {}),
                    style: const TextStyle(fontFamily: 'monospace', fontSize: 13),
                    decoration: const InputDecoration(
                      alignLabelWithHint: true,
                      border: OutlineInputBorder(),
                      hintText: 'Escribe el código HTML enriquecido o plantilla...',
                    ),
                  ),
                  const SizedBox(height: 16),

                  Row(
                    children: [
                      if (_selectedTemplate?.id != null)
                        OutlinedButton.icon(
                          icon: const Icon(Icons.delete_outline, color: Colors.red),
                          label: const Text('Eliminar Plantilla', style: TextStyle(color: Colors.red)),
                          onPressed: () {
                            cubit.deleteTemplate(_selectedTemplate!.id!);
                            setState(() => _selectedTemplate = null);
                          },
                        ),
                      const Spacer(),
                      FilledButton.icon(
                        icon: const Icon(Icons.save_rounded),
                        label: const Text('Guardar y Aplicar Plantilla'),
                        onPressed: () {
                          final payload = {
                            if (_selectedTemplate?.id != null) 'id': _selectedTemplate!.id,
                            'name': _nameController.text.trim(),
                            'content': _contentController.text,
                            'platform': _platform,
                            'is_default': _isDefault,
                          };
                          cubit.saveTemplate(payload);
                        },
                      ),
                    ],
                  ),
                ],
              ),
            ),

            // RIGHT: Live Interactive Telegram Simulator
            Expanded(
              flex: 4,
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: TelegramSimulator(
                  templateContent: _contentController.text,
                ),
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _formatButton(String label, VoidCallback onPressed) {
    return OutlinedButton(
      style: OutlinedButton.styleFrom(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        minimumSize: Size.zero,
        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
      ),
      onPressed: onPressed,
      child: Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
    );
  }
}
""")

# =========================================================================
# 6. workgroups_tab.dart
# =========================================================================
write_file(r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\views\widgets\workgroups_tab.dart", """import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '/features/zeepub_editorial/presentation/cubit/zeepub_editorial_cubit.dart';
import '/features/zeepub_editorial/presentation/cubit/zeepub_editorial_state.dart';

class ZeepubWorkgroupsTab extends StatefulWidget {
  const ZeepubWorkgroupsTab({super.key});

  @override
  State<ZeepubWorkgroupsTab> createState() => _ZeepubWorkgroupsTabState();
}

class _ZeepubWorkgroupsTabState extends State<ZeepubWorkgroupsTab> {
  final TextEditingController _searchController = TextEditingController();

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final tt = Theme.of(context).textTheme;

    return BlocBuilder<ZeepubEditorialCubit, ZeepubEditorialState>(
      builder: (context, state) {
        final query = _searchController.text.toLowerCase().trim();
        final groups = state.workgroups.where((g) {
          if (query.isEmpty) return true;
          return g.name.toLowerCase().contains(query) ||
              g.siglas.toLowerCase().contains(query) ||
              g.description.toLowerCase().contains(query);
        }).toList();

        return Column(
          children: [
            // Search Bar & Stats
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _searchController,
                      decoration: InputDecoration(
                        hintText: 'Buscar fansub o editorial por nombre o siglas...',
                        prefixIcon: const Icon(Icons.search),
                        suffixIcon: _searchController.text.isNotEmpty
                            ? IconButton(
                                icon: const Icon(Icons.clear),
                                onPressed: () {
                                  _searchController.clear();
                                  setState(() {});
                                },
                              )
                            : null,
                        isDense: true,
                        border: const OutlineInputBorder(),
                      ),
                      onChanged: (_) => setState(() {}),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Chip(
                    avatar: const Icon(Icons.groups_rounded, size: 16),
                    label: Text('${groups.length} fansubs registrados'),
                  ),
                ],
              ),
            ),

            // Grid of Workgroups
            Expanded(
              child: groups.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.groups_outlined, size: 48, color: cs.onSurfaceVariant),
                          const SizedBox(height: 12),
                          Text('No se encontraron fansubs con el filtro actual.', style: tt.bodyMedium),
                        ],
                      ),
                    )
                  : GridView.builder(
                      padding: const EdgeInsets.all(16),
                      gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
                        maxCrossAxisExtent: 360,
                        mainAxisSpacing: 12,
                        crossAxisSpacing: 12,
                        mainAxisExtent: 140,
                      ),
                      itemCount: groups.length,
                      itemBuilder: (context, idx) {
                        final g = groups[idx];
                        return Card(
                          elevation: 0,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                            side: BorderSide(color: cs.outlineVariant.withValues(alpha: 0.5)),
                          ),
                          child: Padding(
                            padding: const EdgeInsets.all(12),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    CircleAvatar(
                                      radius: 16,
                                      backgroundColor: cs.primaryContainer,
                                      child: Text(
                                        g.siglas.isNotEmpty ? g.siglas.substring(0, g.siglas.length > 3 ? 3 : g.siglas.length) : (g.name.isNotEmpty ? g.name[0] : 'F'),
                                        style: TextStyle(color: cs.onPrimaryContainer, fontWeight: FontWeight.bold, fontSize: 11),
                                      ),
                                    ),
                                    const SizedBox(width: 10),
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            g.name,
                                            style: tt.titleSmall?.copyWith(fontWeight: FontWeight.bold),
                                            maxLines: 1,
                                            overflow: TextOverflow.ellipsis,
                                          ),
                                          if (g.siglas.isNotEmpty)
                                            Text(
                                              'Siglas: ${g.siglas}',
                                              style: tt.labelSmall?.copyWith(color: cs.primary),
                                            ),
                                        ],
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 8),
                                Expanded(
                                  child: Text(
                                    g.description.isNotEmpty ? g.description : (g.url.isNotEmpty ? g.url : 'Fansub activo en la comunidad.'),
                                    style: tt.bodySmall?.copyWith(color: cs.onSurfaceVariant),
                                    maxLines: 2,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
            ),
          ],
        );
      },
    );
  }
}
""")

# =========================================================================
# 7. calendar_tab.dart
# =========================================================================
write_file(r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\views\widgets\calendar_tab.dart", """import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '/features/zeepub_editorial/presentation/cubit/zeepub_editorial_cubit.dart';
import '/features/zeepub_editorial/presentation/cubit/zeepub_editorial_state.dart';

class ZeepubCalendarTab extends StatefulWidget {
  const ZeepubCalendarTab({super.key});

  @override
  State<ZeepubCalendarTab> createState() => _ZeepubCalendarTabState();
}

class _ZeepubCalendarTabState extends State<ZeepubCalendarTab> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ZeepubEditorialCubit>().loadQueue();
    });
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final tt = Theme.of(context).textTheme;

    return BlocBuilder<ZeepubEditorialCubit, ZeepubEditorialState>(
      builder: (context, state) {
        final cubit = context.read<ZeepubEditorialCubit>();
        final queue = state.queue;

        return Column(
          children: [
            // Header stats
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
              child: Row(
                children: [
                  Icon(Icons.calendar_month_rounded, color: cs.primary, size: 20),
                  const SizedBox(width: 8),
                  Text('COLA DE PUBLICACIONES AGENDADAS', style: tt.labelLarge?.copyWith(fontWeight: FontWeight.bold, letterSpacing: 0.5)),
                  const Spacer(),
                  IconButton(
                    icon: const Icon(Icons.refresh),
                    tooltip: 'Actualizar agenda',
                    onPressed: () => cubit.loadQueue(),
                  ),
                ],
              ),
            ),
            const Divider(height: 1),

            // Queue List
            Expanded(
              child: queue.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.event_available_rounded, size: 48, color: cs.onSurfaceVariant),
                          const SizedBox(height: 12),
                          Text('No hay publicaciones programadas pendientes en la agenda.', style: tt.bodyMedium),
                          const SizedBox(height: 6),
                          Text('Puedes agendar publicaciones desde la vista de cada tomo.', style: tt.bodySmall?.copyWith(color: cs.onSurfaceVariant)),
                        ],
                      ),
                    )
                  : ListView.separated(
                      padding: const EdgeInsets.all(16),
                      itemCount: queue.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 10),
                      itemBuilder: (context, idx) {
                        final item = queue[idx];
                        return Card(
                          elevation: 0,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                            side: BorderSide(color: cs.outlineVariant.withValues(alpha: 0.5)),
                          ),
                          child: Padding(
                            padding: const EdgeInsets.all(12),
                            child: Row(
                              children: [
                                Container(
                                  padding: const EdgeInsets.all(10),
                                  decoration: BoxDecoration(
                                    color: item.status == 'failed' ? Colors.red.withValues(alpha: 0.1) : cs.primaryContainer.withValues(alpha: 0.5),
                                    borderRadius: BorderRadius.circular(10),
                                  ),
                                  child: Icon(
                                    item.status == 'failed' ? Icons.error_outline_rounded : Icons.schedule_rounded,
                                    color: item.status == 'failed' ? Colors.red : cs.primary,
                                    size: 24,
                                  ),
                                ),
                                const SizedBox(width: 14),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        item.bookTitle.isNotEmpty ? item.bookTitle : 'Tomo ${item.bookHash}',
                                        style: tt.titleSmall?.copyWith(fontWeight: FontWeight.bold),
                                      ),
                                      const SizedBox(height: 3),
                                      Row(
                                        children: [
                                          Icon(Icons.send_rounded, size: 12, color: cs.onSurfaceVariant),
                                          const SizedBox(width: 4),
                                          Text(
                                            item.channelName.isNotEmpty ? item.channelName : 'Canal ${item.channelId}',
                                            style: tt.labelSmall?.copyWith(color: cs.onSurfaceVariant),
                                          ),
                                          const SizedBox(width: 12),
                                          Icon(Icons.access_time_filled_rounded, size: 12, color: cs.primary),
                                          const SizedBox(width: 4),
                                          Text(
                                            item.scheduledAt,
                                            style: tt.labelSmall?.copyWith(color: cs.primary, fontWeight: FontWeight.bold),
                                          ),
                                        ],
                                      ),
                                      if (item.errorMessage != null && item.errorMessage!.isNotEmpty)
                                        Padding(
                                          padding: const EdgeInsets.only(top: 4),
                                          child: Text(
                                            'Error: ${item.errorMessage}',
                                            style: tt.bodySmall?.copyWith(color: Colors.red),
                                          ),
                                        ),
                                    ],
                                  ),
                                ),
                                Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    if (item.status == 'failed')
                                      IconButton(
                                        icon: const Icon(Icons.replay_rounded),
                                        tooltip: 'Reintentar publicación',
                                        onPressed: () => cubit.retryQueueItem(item.id),
                                      ),
                                    IconButton(
                                      icon: const Icon(Icons.cancel_outlined, color: Colors.red),
                                      tooltip: 'Cancelar programación',
                                      onPressed: () => cubit.cancelQueueItem(item.id),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
            ),
          ],
        );
      },
    );
  }
}
""")

# =========================================================================
# 8. posts_tab.dart
# =========================================================================
write_file(r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\views\widgets\posts_tab.dart", """import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '/features/zeepub_editorial/presentation/cubit/zeepub_editorial_cubit.dart';
import '/features/zeepub_editorial/presentation/cubit/zeepub_editorial_state.dart';

class ZeepubPostsTab extends StatefulWidget {
  const ZeepubPostsTab({super.key});

  @override
  State<ZeepubPostsTab> createState() => _ZeepubPostsTabState();
}

class _ZeepubPostsTabState extends State<ZeepubPostsTab> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ZeepubEditorialCubit>().loadPosts();
    });
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final tt = Theme.of(context).textTheme;

    return BlocBuilder<ZeepubEditorialCubit, ZeepubEditorialState>(
      builder: (context, state) {
        final cubit = context.read<ZeepubEditorialCubit>();
        final posts = state.posts;

        return Column(
          children: [
            // Header
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
              child: Row(
                children: [
                  Icon(Icons.history_rounded, color: cs.primary, size: 20),
                  const SizedBox(width: 8),
                  Text('HISTORIAL DE PUBLICACIONES ENVIADAS', style: tt.labelLarge?.copyWith(fontWeight: FontWeight.bold, letterSpacing: 0.5)),
                  const Spacer(),
                  IconButton(
                    icon: const Icon(Icons.refresh),
                    tooltip: 'Actualizar historial',
                    onPressed: () => cubit.loadPosts(),
                  ),
                ],
              ),
            ),
            const Divider(height: 1),

            // Posts List
            Expanded(
              child: posts.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.mark_chat_read_outlined, size: 48, color: cs.onSurfaceVariant),
                          const SizedBox(height: 12),
                          Text('No hay publicaciones registradas en el historial.', style: tt.bodyMedium),
                        ],
                      ),
                    )
                  : ListView.separated(
                      padding: const EdgeInsets.all(16),
                      itemCount: posts.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 8),
                      itemBuilder: (context, idx) {
                        final post = posts[idx];
                        return Card(
                          elevation: 0,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                            side: BorderSide(color: cs.outlineVariant.withValues(alpha: 0.4)),
                          ),
                          child: ListTile(
                            leading: CircleAvatar(
                              backgroundColor: post.platform == 'facebook' ? Colors.blue.shade900 : Colors.lightBlue.shade800,
                              child: Icon(
                                post.platform == 'facebook' ? Icons.facebook : Icons.send_rounded,
                                color: Colors.white,
                                size: 18,
                              ),
                            ),
                            title: Text(
                              post.bookTitle.isNotEmpty ? post.bookTitle : 'Tomo ${post.bookHash}',
                              style: tt.bodyMedium?.copyWith(fontWeight: FontWeight.bold),
                            ),
                            subtitle: Row(
                              children: [
                                Text(
                                  post.channelName.isNotEmpty ? post.channelName : 'Canal ${post.channelId}',
                                  style: tt.labelSmall?.copyWith(color: cs.onSurfaceVariant),
                                ),
                                const SizedBox(width: 12),
                                Text(
                                  post.publishedAt,
                                  style: tt.labelSmall?.copyWith(color: cs.primary),
                                ),
                              ],
                            ),
                            trailing: post.messageId != null
                                ? Chip(
                                    label: Text('Msg ID: ${post.messageId}', style: const TextStyle(fontSize: 10)),
                                    padding: EdgeInsets.zero,
                                  )
                                : null,
                          ),
                        );
                      },
                    ),
            ),
          ],
        );
      },
    );
  }
}
""")

# =========================================================================
# 9. zeepub_publisher_view.dart
# =========================================================================
write_file(r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\views\zeepub_publisher_view.dart", """import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '/features/zeepub_editorial/data/models/zeepub_channel.dart';
import '/features/zeepub_editorial/data/models/zeepub_series.dart';
import '/features/zeepub_editorial/data/models/zeepub_template.dart';
import '/features/zeepub_editorial/data/models/zeepub_volume.dart';
import '/features/zeepub_editorial/presentation/cubit/zeepub_editorial_cubit.dart';
import '/features/zeepub_editorial/presentation/cubit/zeepub_editorial_state.dart';
import 'widgets/telegram_simulator.dart';

class ZeepubPublisherView extends StatefulWidget {
  final ZeepubVolume volume;
  final String baseUrl;
  final VoidCallback onBack;

  const ZeepubPublisherView({
    super.key,
    required this.volume,
    required this.baseUrl,
    required this.onBack,
  });

  @override
  State<ZeepubPublisherView> createState() => _ZeepubPublisherViewState();
}

class _ZeepubPublisherViewState extends State<ZeepubPublisherView> {
  ZeepubChannel? _selectedChannel;
  ZeepubTemplate? _selectedTemplate;
  late final TextEditingController _captionController;
  bool _publishNow = true;
  DateTime _scheduledDate = DateTime.now().add(const Duration(hours: 1));
  TimeOfDay _scheduledTime = TimeOfDay.fromDateTime(DateTime.now().add(const Duration(hours: 1)));
  bool _sendAsFile = true;

  final List<String> _variables = [
    '{serie}',
    '{volumen}',
    '{titulo}',
    '{autor}',
    '{illustrator}',
    '{traductor}',
    '{editorial}',
    '{sinopsis}',
    '{demography}',
    '{genres}',
    '{tomoid}',
    '{fecha}',
    '{published_at}',
    '{slug}',
    '{download_link}',
    '{layout_by}',
  ];

  @override
  void initState() {
    super.initState();
    _captionController = TextEditingController();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final cubit = context.read<ZeepubEditorialCubit>();
      cubit.loadChannels();
      cubit.loadTemplates();
    });
  }

  @override
  void dispose() {
    _captionController.dispose();
    super.dispose();
  }

  void _insertTag(String tag) {
    final text = _captionController.text;
    final selection = _captionController.selection;
    final start = selection.start >= 0 ? selection.start : text.length;
    final end = selection.end >= 0 ? selection.end : text.length;
    final newText = text.replaceRange(start, end, tag);
    _captionController.value = TextEditingValue(
      text: newText,
      selection: TextSelection.collapsed(offset: start + tag.length),
    );
    setState(() {});
  }

  void _wrapTag(String open, String close) {
    final text = _captionController.text;
    final selection = _captionController.selection;
    if (selection.start >= 0 && selection.end > selection.start) {
      final selectedText = text.substring(selection.start, selection.end);
      final newText = text.replaceRange(selection.start, selection.end, '$open$selectedText$close');
      _captionController.value = TextEditingValue(
        text: newText,
        selection: TextSelection.collapsed(offset: selection.end + open.length + close.length),
      );
    } else {
      _insertTag('$open$close');
    }
    setState(() {});
  }

  String _buildCoverUrl() {
    if (widget.volume.coverUrl == null || widget.volume.coverUrl!.isEmpty) return '';
    if (widget.volume.coverUrl!.startsWith('http')) return widget.volume.coverUrl!;
    final cleanBase = widget.baseUrl.replaceAll(RegExp(r"/+$"), "");
    final cleanPath = widget.volume.coverUrl!.startsWith('/') ? widget.volume.coverUrl! : '/${widget.volume.coverUrl!}';
    return '$cleanBase$cleanPath';
  }

  Future<void> _handlePublish(ZeepubEditorialCubit cubit) async {
    final customCaption = _captionController.text.trim();

    if (_publishNow) {
      await cubit.publishNow(
        bookHash: widget.volume.bookHash,
        channelId: _selectedChannel?.id,
        templateId: _selectedTemplate?.id,
        customCaption: customCaption.isNotEmpty ? customCaption : null,
        sendAsFile: _sendAsFile,
      );
    } else {
      final dt = DateTime(
        _scheduledDate.year,
        _scheduledDate.month,
        _scheduledDate.day,
        _scheduledTime.hour,
        _scheduledTime.minute,
      );
      await cubit.schedulePublication(
        bookHash: widget.volume.bookHash,
        scheduledAtIso: dt.toIso8601String(),
        channelId: _selectedChannel?.id,
        templateId: _selectedTemplate?.id,
        customCaption: customCaption.isNotEmpty ? customCaption : null,
        sendAsFile: _sendAsFile,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final tt = Theme.of(context).textTheme;
    final coverUrl = _buildCoverUrl();

    return BlocConsumer<ZeepubEditorialCubit, ZeepubEditorialState>(
      listener: (context, state) {
        if (state.successMessage != null) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(state.successMessage!),
              backgroundColor: Colors.green.shade800,
            ),
          );
          widget.onBack();
        }
      },
      builder: (context, state) {
        final cubit = context.read<ZeepubEditorialCubit>();
        final channels = state.channels;
        final templates = state.templates;

        if (channels.isNotEmpty && _selectedChannel == null) {
          _selectedChannel = channels.firstWhere((c) => c.isDefault, orElse: () => channels.first);
        }

        if (templates.isNotEmpty && _selectedTemplate == null) {
          _selectedTemplate = templates.firstWhere((t) => t.isDefault, orElse: () => templates.first);
          if (_captionController.text.isEmpty && _selectedTemplate != null) {
            _captionController.text = _selectedTemplate!.content;
          }
        }

        final ZeepubSeries? series = state.seriesList.cast<ZeepubSeries?>().firstWhere(
              (s) => s != null && (s.id == widget.volume.seriesId || s.name == widget.volume.seriesName),
              orElse: () => null,
            );

        return Scaffold(
          appBar: AppBar(
            leading: IconButton(
              icon: const Icon(Icons.arrow_back),
              tooltip: 'Volver a Tomos',
              onPressed: widget.onBack,
            ),
            title: Row(
              children: [
                const Icon(Icons.send_rounded, color: Color(0xFF38BDF8)),
                const SizedBox(width: 10),
                Text('Publicador Oficial Telegram · ${widget.volume.title}'),
              ],
            ),
          ),
          body: Row(
            children: [
              // LEFT COLUMN: PUBLISHING CONFIGURATION & EDITOR
              Expanded(
                flex: 5,
                child: ListView(
                  padding: const EdgeInsets.all(20),
                  children: [
                    // BOOK SUMMARY CARD
                    Card(
                      elevation: 0,
                      color: cs.surfaceContainerHighest.withValues(alpha: 0.4),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                        side: BorderSide(color: cs.outlineVariant.withValues(alpha: 0.3)),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Row(
                          children: [
                            ClipRRect(
                              borderRadius: BorderRadius.circular(6),
                              child: coverUrl.isNotEmpty
                                  ? Image.network(
                                      coverUrl,
                                      width: 50,
                                      height: 70,
                                      fit: BoxFit.cover,
                                      errorBuilder: (_, __, ___) => Container(
                                        width: 50,
                                        height: 70,
                                        color: cs.surfaceContainerHighest,
                                        child: const Icon(Icons.book, size: 24),
                                      ),
                                    )
                                  : Container(
                                      width: 50,
                                      height: 70,
                                      color: cs.surfaceContainerHighest,
                                      child: const Icon(Icons.book, size: 24),
                                    ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    widget.volume.englishTitle.isNotEmpty ? widget.volume.englishTitle : widget.volume.title,
                                    style: tt.titleSmall?.copyWith(fontWeight: FontWeight.bold),
                                  ),
                                  Text(
                                    'Volumen ${widget.volume.volume ?? 1} · Fansub: ${widget.volume.publisher ?? "Oficial"}',
                                    style: tt.labelSmall?.copyWith(color: cs.primary),
                                  ),
                                  Text(
                                    'Trad: ${widget.volume.translator ?? "N/A"} · ${widget.volume.filename ?? ""}',
                                    style: tt.bodySmall?.copyWith(color: cs.onSurfaceVariant),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // CHANNEL & TEMPLATE SELECTORS
                    Row(
                      children: [
                        // Channel Dropdown
                        Expanded(
                          child: DropdownButtonFormField<int>(
                            initialValue: _selectedChannel?.id,
                            decoration: const InputDecoration(
                              labelText: 'Canal de Destino',
                              prefixIcon: Icon(Icons.send_rounded),
                              border: OutlineInputBorder(),
                            ),
                            items: channels.map((c) {
                              return DropdownMenuItem<int>(
                                value: c.id,
                                child: Text(c.name.isNotEmpty ? c.name : c.channelId),
                              );
                            }).toList(),
                            onChanged: (id) {
                              if (id != null) {
                                setState(() {
                                  _selectedChannel = channels.firstWhere((c) => c.id == id);
                                });
                              }
                            },
                          ),
                        ),
                        const SizedBox(width: 12),

                        // Template Dropdown
                        Expanded(
                          child: DropdownButtonFormField<int>(
                            initialValue: _selectedTemplate?.id,
                            decoration: const InputDecoration(
                              labelText: 'Plantilla Editorial',
                              prefixIcon: Icon(Icons.view_quilt),
                              border: OutlineInputBorder(),
                            ),
                            items: templates.map((t) {
                              return DropdownMenuItem<int>(
                                value: t.id,
                                child: Text(t.name),
                              );
                            }).toList(),
                            onChanged: (id) {
                              if (id != null) {
                                final tpl = templates.firstWhere((t) => t.id == id);
                                setState(() {
                                  _selectedTemplate = tpl;
                                  _captionController.text = tpl.content;
                                });
                              }
                            },
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),

                    // PUBLICATION MODE TABS (NOW vs SCHEDULED)
                    SegmentedButton<bool>(
                      segments: const [
                        ButtonSegment(
                          value: true,
                          icon: Icon(Icons.flash_on_rounded),
                          label: Text('Publicar Ahora'),
                        ),
                        ButtonSegment(
                          value: false,
                          icon: Icon(Icons.schedule_rounded),
                          label: Text('Programar Fecha/Hora'),
                        ),
                      ],
                      selected: {_publishNow},
                      onSelectionChanged: (set) => setState(() => _publishNow = set.first),
                    ),
                    const SizedBox(height: 12),

                    // SCHEDULE DATE/TIME PICKERS
                    if (!_publishNow)
                      Card(
                        elevation: 0,
                        color: cs.primaryContainer.withValues(alpha: 0.2),
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Row(
                            children: [
                              Expanded(
                                child: OutlinedButton.icon(
                                  icon: const Icon(Icons.calendar_today_rounded),
                                  label: Text('${_scheduledDate.year}-${_scheduledDate.month.toString().padLeft(2, "0")}-${_scheduledDate.day.toString().padLeft(2, "0")}'),
                                  onPressed: () async {
                                    final picked = await showDatePicker(
                                      context: context,
                                      initialDate: _scheduledDate,
                                      firstDate: DateTime.now(),
                                      lastDate: DateTime.now().add(const Duration(days: 365)),
                                    );
                                    if (picked != null) setState(() => _scheduledDate = picked);
                                  },
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: OutlinedButton.icon(
                                  icon: const Icon(Icons.access_time_rounded),
                                  label: Text('${_scheduledTime.hour.toString().padLeft(2, "0")}:${_scheduledTime.minute.toString().padLeft(2, "0")}'),
                                  onPressed: () async {
                                    final picked = await showTimePicker(
                                      context: context,
                                      initialTime: _scheduledTime,
                                    );
                                    if (picked != null) setState(() => _scheduledTime = picked);
                                  },
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),

                    const SizedBox(height: 16),

                    // OPTIONS (SEND AS EPUB DOCUMENT)
                    CheckboxListTile(
                      value: _sendAsFile,
                      title: const Text('Adjuntar archivo EPUB al mensaje'),
                      subtitle: const Text('Envia el documento EPUB real junto con la ficha estructurada'),
                      dense: true,
                      controlAffinity: ListTileControlAffinity.leading,
                      contentPadding: EdgeInsets.zero,
                      onChanged: (val) => setState(() => _sendAsFile = val ?? true),
                    ),
                    const SizedBox(height: 12),

                    // COPY EDITOR TOOLBAR
                    Text('MENSAJE / CAPTION PERSONALIZADO', style: tt.labelLarge?.copyWith(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 6),
                    Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      children: [
                        _formatButton('B', () => _wrapTag('<b>', '</b>')),
                        _formatButton('I', () => _wrapTag('<i>', '</i>')),
                        _formatButton('U', () => _wrapTag('<u>', '</u>')),
                        _formatButton('S', () => _wrapTag('<s>', '</s>')),
                        _formatButton('Cita', () => _wrapTag('<blockquote>', '</blockquote>')),
                        _formatButton('Expandible', () => _wrapTag('<details><summary>Titulo</summary>', '</details>')),
                        _formatButton('H', () => _wrapTag('<h3>', '</h3>')),
                        _formatButton('Enlace', () => _wrapTag('<a href="URL">', '</a>')),
                        _formatButton('Condicional [?]', () => _wrapTag('[?volumen]', '[/?]')),
                      ],
                    ),
                    const SizedBox(height: 8),

                    // VARIABLE CHIPS
                    Text('VARIABLES DINÁMICAS (Haz clic para insertar):', style: tt.labelSmall?.copyWith(color: cs.onSurfaceVariant)),
                    const SizedBox(height: 6),
                    Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      children: [
                        for (final v in _variables)
                          ActionChip(
                            label: Text(v, style: const TextStyle(fontSize: 11, fontFamily: 'monospace')),
                            padding: EdgeInsets.zero,
                            onPressed: () => _insertTag(v),
                          ),
                      ],
                    ),
                    const SizedBox(height: 12),

                    // CAPTION TEXT AREA
                    TextField(
                      controller: _captionController,
                      maxLines: 12,
                      onChanged: (_) => setState(() {}),
                      style: const TextStyle(fontFamily: 'monospace', fontSize: 13),
                      decoration: const InputDecoration(
                        labelText: 'Plantilla de Texto del Mensaje',
                        alignLabelWithHint: true,
                        border: OutlineInputBorder(),
                        hintText: 'Escribe o ajusta el copy para esta publicación...',
                      ),
                    ),
                    const SizedBox(height: 24),

                    // ACTION BUTTON
                    SizedBox(
                      height: 48,
                      child: FilledButton.icon(
                        style: FilledButton.styleFrom(
                          backgroundColor: const Color(0xFF38BDF8),
                          foregroundColor: Colors.black,
                        ),
                        icon: state.saving
                            ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black))
                            : Icon(_publishNow ? Icons.send_rounded : Icons.calendar_month_rounded),
                        label: Text(
                          _publishNow ? 'Publicar Inmediatamente en Canal' : 'Guardar y Programar Publicación',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                        ),
                        onPressed: state.saving ? null : () => _handlePublish(cubit),
                      ),
                    ),
                  ],
                ),
              ),

              // RIGHT COLUMN: TELEGRAM DESKTOP SIMULATOR (LIVE PREVIEW)
              Expanded(
                flex: 5,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: TelegramSimulator(
                    templateContent: _captionController.text,
                    volume: widget.volume,
                    series: series,
                    channel: _selectedChannel,
                    customCoverUrl: coverUrl,
                    sendAsFile: _sendAsFile,
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _formatButton(String label, VoidCallback onPressed) {
    return OutlinedButton(
      style: OutlinedButton.styleFrom(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        minimumSize: Size.zero,
        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
      ),
      onPressed: onPressed,
      child: Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
    );
  }
}
""")

# =========================================================================
# 10. zeepub_editorial_view.dart
# =========================================================================
write_file(r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\views\zeepub_editorial_view.dart", """import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '/features/zeepub_editorial/presentation/cubit/zeepub_editorial_cubit.dart';
import '/features/zeepub_editorial/presentation/cubit/zeepub_editorial_state.dart';
import 'widgets/calendar_tab.dart';
import 'widgets/posts_tab.dart';
import 'widgets/series_list_widget.dart';
import 'widgets/templates_tab.dart';
import 'widgets/volume_card.dart';
import 'widgets/workgroups_tab.dart';
import 'zeepub_publisher_view.dart';
import 'zeepub_volume_edit_view.dart';

class ZeepubEditorialView extends StatefulWidget {
  const ZeepubEditorialView({super.key});

  @override
  State<ZeepubEditorialView> createState() => _ZeepubEditorialViewState();
}

class _ZeepubEditorialViewState extends State<ZeepubEditorialView> with SingleTickerProviderStateMixin {
  late final TabController _tabController;
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 6, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ZeepubEditorialCubit>().init();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    _searchController.dispose();
    super.dispose();
  }

  void _showConfigServerDialog(BuildContext context, String currentUrl) {
    final controller = TextEditingController(text: currentUrl);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.dns_rounded),
            SizedBox(width: 8),
            Text('URL del Servidor ZeePub'),
          ],
        ),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(
            labelText: 'Base URL (ej. http://127.0.0.1:8001)',
            hintText: 'http://localhost:8001',
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
              Navigator.of(ctx).pop();
            },
            child: const Text('Guardar'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final tt = Theme.of(context).textTheme;

    return BlocConsumer<ZeepubEditorialCubit, ZeepubEditorialState>(
      listener: (context, state) {
        if (state.errorMessage != null) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(state.errorMessage!),
              backgroundColor: cs.error,
            ),
          );
          context.read<ZeepubEditorialCubit>().clearNotifications();
        }
        if (state.successMessage != null) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(state.successMessage!),
              backgroundColor: Colors.green.shade800,
            ),
          );
          context.read<ZeepubEditorialCubit>().clearNotifications();
        }
      },
      builder: (BuildContext context, ZeepubEditorialState state) {
        final cubit = context.read<ZeepubEditorialCubit>();

        // 1. DEDICATED FULL-PAGE PUBLISHER VIEW
        if (state.publishingVolume != null) {
          return ZeepubPublisherView(
            volume: state.publishingVolume!,
            baseUrl: state.baseUrl,
            onBack: () => cubit.closePublisher(),
          );
        }

        // 2. DEDICATED FULL-PAGE VOLUME EDITOR VIEW
        if (state.activeVolume != null) {
          return ZeepubVolumeEditView(
            volume: state.activeVolume!,
            seriesList: state.seriesList,
            workgroups: state.workgroups,
            baseUrl: state.baseUrl,
            onBack: () => cubit.closeVolumeDetail(),
          );
        }

        return Scaffold(
          appBar: AppBar(
            title: Row(
              children: [
                const Icon(Icons.auto_stories_rounded),
                const SizedBox(width: 10),
                const Text('Consola Editorial ZeePub'),
                const SizedBox(width: 12),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: cs.primaryContainer.withValues(alpha: 0.6),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        width: 7,
                        height: 7,
                        decoration: BoxDecoration(
                          color: state.errorMessage != null ? Colors.red : Colors.green,
                          shape: BoxShape.circle,
                        ),
                      ),
                      const SizedBox(width: 5),
                      Text(
                        state.baseUrl.replaceFirst('http://', '').replaceFirst('https://', ''),
                        style: tt.labelSmall?.copyWith(color: cs.onPrimaryContainer),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            actions: [
              IconButton(
                icon: const Icon(Icons.settings_ethernet),
                tooltip: 'Configurar URL del servidor',
                onPressed: () => _showConfigServerDialog(context, state.baseUrl),
              ),
              IconButton(
                icon: const Icon(Icons.refresh),
                tooltip: 'Recargar Datos',
                onPressed: () => cubit.init(),
              ),
              const SizedBox(width: 8),
            ],
            bottom: TabBar(
              controller: _tabController,
              isScrollable: true,
              tabAlignment: TabAlignment.start,
              tabs: [
                Tab(
                  icon: const Icon(Icons.book_rounded, size: 18),
                  text: 'Tomos (${state.totalVolumes})',
                ),
                Tab(
                  icon: const Icon(Icons.collections_bookmark_rounded, size: 18),
                  text: 'Series (${state.totalSeries})',
                ),
                Tab(
                  icon: const Icon(Icons.groups_rounded, size: 18),
                  text: 'Fansubs (${state.workgroups.length})',
                ),
                Tab(
                  icon: const Icon(Icons.view_quilt, size: 18),
                  text: 'Plantillas (${state.templates.length})',
                ),
                Tab(
                  icon: const Icon(Icons.calendar_month_rounded, size: 18),
                  text: 'Agenda (${state.queue.length})',
                ),
                Tab(
                  icon: const Icon(Icons.history_rounded, size: 18),
                  text: 'Historial (${state.posts.length})',
                ),
              ],
            ),
          ),
          body: TabBarView(
            controller: _tabController,
            children: [
              // TAB 1: VOLUMES LIST
              _buildVolumesTab(context, state, cubit),

              // TAB 2: SERIES LIST
              const SeriesListWidget(),

              // TAB 3: FANSUBS DIRECTORY
              const ZeepubWorkgroupsTab(),

              // TAB 4: TEMPLATES LIBRARY
              const ZeepubTemplatesTab(),

              // TAB 5: PUBLICATION AGENDA
              const ZeepubCalendarTab(),

              // TAB 6: POSTS HISTORY
              const ZeepubPostsTab(),
            ],
          ),
        );
      },
    );
  }

  Widget _buildVolumesTab(BuildContext context, ZeepubEditorialState state, ZeepubEditorialCubit cubit) {
    final cs = Theme.of(context).colorScheme;

    return Column(
      children: [
        // Filter Bar
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _searchController,
                  decoration: InputDecoration(
                    hintText: 'Buscar por título, serie, autor o traductor...',
                    prefixIcon: const Icon(Icons.search),
                    suffixIcon: _searchController.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear),
                            onPressed: () {
                              _searchController.clear();
                              cubit.loadVolumes(page: 1, query: '');
                            },
                          )
                        : null,
                    isDense: true,
                    border: const OutlineInputBorder(),
                  ),
                  onSubmitted: (val) => cubit.loadVolumes(page: 1, query: val),
                ),
              ),
              const SizedBox(width: 8),
              FilledButton.icon(
                icon: const Icon(Icons.search),
                label: const Text('Buscar'),
                onPressed: () => cubit.loadVolumes(page: 1, query: _searchController.text),
              ),
            ],
          ),
        ),

        // Volumes Grid View
        Expanded(
          child: state.loading && state.volumes.isEmpty
              ? const Center(child: CircularProgressIndicator())
              : state.volumes.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.library_books_rounded, size: 48, color: cs.onSurfaceVariant),
                          const SizedBox(height: 12),
                          const Text('No se encontraron tomos con los filtros actuales.'),
                        ],
                      ),
                    )
                  : GridView.builder(
                      padding: const EdgeInsets.all(16),
                      gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
                        maxCrossAxisExtent: 380,
                        mainAxisSpacing: 12,
                        crossAxisSpacing: 12,
                        mainAxisExtent: 220,
                      ),
                      itemCount: state.volumes.length,
                      itemBuilder: (context, idx) {
                        final vol = state.volumes[idx];
                        return VolumeCard(
                          volume: vol,
                          baseUrl: state.baseUrl,
                          onEdit: () => cubit.openVolumeDetail(vol),
                          onPublish: () => cubit.openPublisher(vol),
                        );
                      },
                    ),
        ),
      ],
    );
  }
}
""")

print("Successfully generated all clean editorial files!")
