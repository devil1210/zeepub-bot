# -*- coding: utf-8 -*-
import os

edit_view_code = r'''import 'package:flutter/material.dart';
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
import 'widgets/telegram_publish_dialog.dart';

class ZeepubVolumeEditView extends StatefulWidget {
  final ZeepubVolume volume;
  final List<ZeepubSeries> seriesList;
  final List<ZeepubWorkgroup> workgroups;
  final String baseUrl;
  final VoidCallback onBack;

  const ZeepubVolumeEditView({
    super.key,
    required this.volume,
    this.seriesList = const [],
    required this.workgroups,
    required this.baseUrl,
    required this.onBack,
  });

  @override
  State<ZeepubVolumeEditView> createState() => _ZeepubVolumeEditViewState();
}

class _ZeepubVolumeEditViewState extends State<ZeepubVolumeEditView> {
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

  // People (List of Actors)
  late List<Actor> _actors;

  // Publication
  late String _bookLanguage;
  late String _bookType;
  late String _publishDate;
  late List<String> _publishers;
  late String _description;

  // Classification
  Demographic? _demographic;
  final Set<String> _selectedGenres = {};
  late String _colorMode;
  late bool _isUncensored;
  int? _rating;

  @override
  void initState() {
    super.initState();
    _syncFromVolume(widget.volume);
  }

  @override
  void didUpdateWidget(ZeepubVolumeEditView oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.volume != widget.volume) {
      _syncFromVolume(widget.volume);
    }
  }

  void _syncFromVolume(ZeepubVolume v) {
    _asin = '';
    _isbn13 = '';
    _isbn10 = '';
    _identifier = v.bookHash.isNotEmpty ? v.bookHash : uuidV7();

    _originalLanguage = OriginalLanguage.ja;
    _isStandalone = v.volume == null && (v.edition ?? '').toLowerCase().contains('único');
    _seriesEnglish = v.englishTitle.isNotEmpty ? v.englishTitle : (v.seriesName ?? '');
    _series = _seriesEnglish;
    _seriesSpanish = v.spanishTitle.isNotEmpty ? v.spanishTitle : '';
    _seriesRomaji = '';
    _seriesNative = '';
    _volumeNumber = v.volume != null ? (v.volume! % 1 == 0 ? v.volume!.toInt().toString() : v.volume!.toString()) : '';

    _titleEnglish = v.englishTitle.isNotEmpty ? v.englishTitle : v.title;
    _title = _titleEnglish;
    _titleSpanish = v.spanishTitle.isNotEmpty ? v.spanishTitle : '';
    _titleRomaji = '';
    _titleNative = '';
    _titleSort = '';

    // Initialize Actors list
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

    // Initialize Publication
    _bookLanguage = 'es';
    _bookType = 'Novela ligera';
    _publishDate = '';
    _publishers = [];
    if (v.publisher != null && v.publisher!.trim().isNotEmpty) {
      _publishers.add(v.publisher!.trim());
    } else {
      _publishers.add('');
    }
    // Clean HTML formatting / <br/> into clean text like in an EPUB reader
    _description = descriptionFromHtml(v.description ?? '');

    // Initialize Classification
    _demographic = Demographic.shounen;
    _colorMode = v.colorMode ?? ((v.filename ?? '').toLowerCase().contains('[color]') ? 'color' : 'bw');
    _isUncensored = v.isUncensored;
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
    if (widget.volume.coverUrl == null || widget.volume.coverUrl!.isEmpty) return '';
    if (widget.volume.coverUrl!.startsWith('http')) return widget.volume.coverUrl!;
    final cleanBase = widget.baseUrl.replaceAll(RegExp(r'/+$'), '');
    final cleanPath = widget.volume.coverUrl!.startsWith('/') ? widget.volume.coverUrl! : '/${widget.volume.coverUrl!}';
    return '$cleanBase$cleanPath';
  }

  Future<void> _handleSave() async {
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
    };

    await cubit.saveVolume(widget.volume.bookHash, payload);
  }

  void _openPublishDialog() {
    showDialog(
      context: context,
      builder: (ctx) => BlocProvider.value(
        value: context.read<ZeepubEditorialCubit>(),
        child: TelegramPublishDialog(
          volume: widget.volume,
          baseUrl: widget.baseUrl,
        ),
      ),
    );
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
              // LEFT PANEL: Cover, File Info, Quick Actions
              Container(
                width: 280,
                padding: const EdgeInsets.all(AppPadding.large),
                decoration: BoxDecoration(
                  border: Border(right: BorderSide(color: cs.outlineVariant.withValues(alpha: 0.5))),
                ),
                child: ListView(
                  children: [
                    Center(
                      child: Container(
                        height: 240,
                        width: 170,
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(AppRadius.medium),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withValues(alpha: 0.3),
                              blurRadius: 10,
                              offset: const Offset(0, 4),
                            ),
                          ],
                        ),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(AppRadius.medium),
                          child: coverUrl.isNotEmpty
                              ? Image.network(
                                  coverUrl,
                                  fit: BoxFit.cover,
                                  errorBuilder: (_, __, ___) => Container(
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
                    const SizedBox(height: 16),
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
                            'Ruta en Servidor:\n${widget.volume.filepath}',
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
                              AppTextField(
                                label: 'Serie en español',
                                value: _seriesSpanish,
                                hint: 'Nombre de la serie en español',
                                onChanged: (v) => setState(() => _seriesSpanish = v),
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
                        AppTextField(
                          label: 'Título en inglés / principal',
                          value: _titleEnglish.isNotEmpty ? _titleEnglish : _title,
                          hint: 'English Title',
                          onChanged: (v) => setState(() {
                            _titleEnglish = v;
                            _title = v;
                          }),
                        ),
                        ResponsiveRow(
                          children: [
                            AppTextField(
                              label: 'Título en español',
                              value: _titleSpanish,
                              hint: 'Título en español',
                              onChanged: (v) => setState(() => _titleSpanish = v),
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
                            AppTextField(
                              label: 'Fecha de publicación',
                              value: _publishDate,
                              hint: 'YYYY-MM-DD',
                              onChanged: (v) => setState(() => _publishDate = v),
                            ),
                          ],
                        ),
                        Text('Editorial o grupo', style: tt.labelLarge),
                        EditableList<String>(
                          items: _publishers,
                          addLabel: 'Añadir editorial',
                          createItem: () => '',
                          onChanged: (v) => setState(() => _publishers = v),
                          itemBuilder: (context, publisher, onChanged, controls) => EditableRow(
                            controls: controls,
                            child: Autocomplete<String>(
                              initialValue: TextEditingValue(text: publisher),
                              optionsBuilder: (textEditingValue) {
                                if (textEditingValue.text.isEmpty) {
                                  return widget.workgroups.map((w) => w.name);
                                }
                                return widget.workgroups
                                    .map((w) => w.name)
                                    .where((name) => name.toLowerCase().contains(textEditingValue.text.toLowerCase()));
                              },
                              onSelected: (selection) => onChanged(selection),
                              fieldViewBuilder: (context, controller, focusNode, onFieldSubmitted) {
                                return TextField(
                                  controller: controller,
                                  focusNode: focusNode,
                                  decoration: const InputDecoration(
                                    labelText: 'Nombre',
                                    hintText: 'Ej. Kadokawa, NovelZ, Saosora Scan',
                                  ),
                                  onChanged: (v) => onChanged(v),
                                );
                              },
                            ),
                          ),
                        ),
                        AppTextField(
                          label: 'Sinopsis',
                          value: _description,
                          hint: 'Escribe o pega aquí la sinopsis completa de la obra...',
                          maxLines: 12,
                          onChanged: (v) => setState(() => _description = v),
                        ),
                      ],
                    ),

                    // SECTION 5: CLASIFICACIÓN (Demografía, Géneros, Edición, Calibre)
                    FormSection(
                      title: 'Clasificación',
                      children: [
                        Text('Demografía', style: tt.labelLarge),
                        Wrap(
                          spacing: AppSpacing.medium,
                          runSpacing: AppSpacing.small,
                          children: [
                            for (final d in Demographic.values)
                              SelectionPill(
                                tooltip: 'Añade también «${d.ageGroup}»',
                                selected: _demographic == d,
                                onTap: () => setState(() {
                                  _demographic = _demographic == d ? null : d;
                                }),
                                child: Text(d.label),
                              ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text('Géneros', style: tt.labelLarge),
                        Wrap(
                          spacing: AppSpacing.medium,
                          runSpacing: AppSpacing.small,
                          children: [
                            for (final genre in literaryGenres)
                              SelectionPill(
                                selected: _selectedGenres.contains(genre),
                                onTap: () => setState(() {
                                  if (_selectedGenres.contains(genre)) {
                                    _selectedGenres.remove(genre);
                                  } else {
                                    _selectedGenres.add(genre);
                                  }
                                }),
                                child: Text(genre),
                              ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text('Edición', style: tt.labelLarge),
                        Wrap(
                          spacing: AppSpacing.medium,
                          runSpacing: AppSpacing.small,
                          children: [
                            SelectionPill(
                              selected: _colorMode == 'color',
                              onTap: () => setState(() {
                                _colorMode = _colorMode == 'color' ? 'bw' : 'color';
                              }),
                              child: const Text('A color'),
                            ),
                            SelectionPill(
                              selected: _isUncensored,
                              onTap: () => setState(() {
                                _isUncensored = !_isUncensored;
                              }),
                              child: const Text('Sin censura'),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        OutlinedDropdown<int?>(
                          label: 'Calificación de calibre',
                          value: _rating,
                          onChanged: (v) => setState(() => _rating = v),
                          items: [
                            const DropdownMenuItem(value: null, child: Text('Sin calificar')),
                            for (var r = 1; r <= 10; r++)
                              DropdownMenuItem(
                                value: r,
                                child: Text('${'★' * (r ~/ 2)}${r.isOdd ? '⯨' : ''}'),
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

class _ActorEditor extends StatefulWidget {
  const _ActorEditor({
    required this.actor,
    required this.onChanged,
    required this.controls,
    required this.defaultScript,
  });

  final Actor actor;
  final ValueChanged<Actor> onChanged;
  final Widget controls;
  final OriginalLanguage defaultScript;

  @override
  State<_ActorEditor> createState() => _ActorEditorState();
}

class _ActorEditorState extends State<_ActorEditor> {
  late final _fileAs = TextEditingController(text: widget.actor.fileAs);
  late var _script = scriptedLanguages
          .where((o) => o.name == widget.actor.scriptName?.lang.trim().toLowerCase())
          .firstOrNull ??
      widget.defaultScript;

  @override
  void dispose() {
    _fileAs.dispose();
    super.dispose();
  }

  void _onNameChanged(String name) {
    final actor = widget.actor;
    final follows = actor.fileAs.isEmpty || actor.fileAs == fileAsFor(actor.name);
    final fileAs = follows ? fileAsFor(name) : actor.fileAs;
    if (fileAs != _fileAs.text) _fileAs.text = fileAs;
    widget.onChanged(actor.copyWith(name: name, fileAs: fileAs));
  }

  void _onScriptChanged(OriginalLanguage script, String text) {
    setState(() => _script = script);
    widget.onChanged(
      widget.actor.copyWith(
        altNames: text.trim().isEmpty ? const [] : [LocalizedText(lang: script.name, text: text)],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final actor = widget.actor;
    final scriptText = actor.scriptName?.text ?? '';
    return Card.outlined(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(
          AppPadding.medium + AppPadding.small,
          AppPadding.medium + AppPadding.small,
          AppPadding.small,
          AppPadding.medium + AppPadding.small,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          spacing: AppSpacing.medium + AppSpacing.small,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              spacing: AppSpacing.medium,
              children: [
                Expanded(
                  child: ResponsiveRow(
                    children: [
                      AppTextField(label: 'Nombre', value: actor.name, onChanged: _onNameChanged),
                      if (actor.name.trim().isNotEmpty)
                        TextField(
                          controller: _fileAs,
                          onChanged: (v) => widget.onChanged(actor.copyWith(fileAs: v)),
                          decoration: const InputDecoration(labelText: 'Nombre para ordenar'),
                        ),
                    ],
                  ),
                ),
                widget.controls,
              ],
            ),
            Wrap(
              spacing: AppSpacing.medium,
              runSpacing: AppSpacing.small,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                Text(actor.isCreator ? 'Creador:' : 'Colaborador:', style: Theme.of(context).textTheme.labelLarge),
                for (final role in actor.roles)
                  TagPill(
                    label: role.label,
                    tooltip: 'marc:relators ${role.name}',
                    onRemove: actor.roles.length == 1 ? null : () => widget.onChanged(actor.copyWith(roles: [...actor.roles]..remove(role))),
                  ),
                PopupMenuButton<MarcRelator>(
                  tooltip: 'Añadir función',
                  icon: const Icon(Icons.add_circle_outline, size: 20),
                  onSelected: (role) => widget.onChanged(actor.copyWith(roles: [...actor.roles, role])),
                  itemBuilder: (_) => [
                    for (final role in MarcRelator.values)
                      if (!actor.roles.contains(role)) PopupMenuItem(value: role, child: Text('${role.label} (${role.name})')),
                  ],
                ),
              ],
            ),
            ResponsiveRow(
              widths: const [languageColumnWidth, null],
              children: [
                OutlinedDropdown<OriginalLanguage>(
                  label: 'Escritura original',
                  value: _script,
                  onChanged: (v) => v == null ? null : _onScriptChanged(v, scriptText),
                  items: [for (final o in scriptedLanguages) DropdownMenuItem(value: o, child: Text(o.label))],
                ),
                AppTextField(
                  label: 'Nombre en ${_script.label.toLowerCase()}',
                  value: scriptText,
                  helper: 'Opcional. En los créditos va como ruby sobre el nombre.',
                  onChanged: (v) => _onScriptChanged(_script, v),
                ),
              ],
            ),
            if (actor.isTranslator)
              ResponsiveRow(
                children: [
                  OutlinedDropdown<String>(
                    label: 'Traducido del',
                    value: actor.fromLang,
                    onChanged: (v) => widget.onChanged(actor.copyWith(fromLang: v ?? '')),
                    items: [
                      const DropdownMenuItem(value: '', child: Text('No se menciona')),
                      for (final MapEntry(key: code, value: name) in bookLanguages.entries) DropdownMenuItem(value: code, child: Text(name)),
                    ],
                  ),
                  OutlinedDropdown<String>(
                    label: 'Traducido al',
                    value: actor.toLang,
                    onChanged: (v) => widget.onChanged(actor.copyWith(toLang: v ?? '')),
                    items: [
                      const DropdownMenuItem(value: '', child: Text('No se menciona')),
                      for (final MapEntry(key: code, value: name) in bookLanguages.entries) DropdownMenuItem(value: code, child: Text(name)),
                    ],
                  ),
                ],
              ),
          ],
        ),
      ),
    );
  }
}

class _BookTypeField extends StatelessWidget {
  const _BookTypeField({required this.value, required this.onChanged});

  final String value;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    return Autocomplete<String>(
      initialValue: TextEditingValue(text: value),
      optionsBuilder: (v) => bookTypes.where((t) => t.toLowerCase().contains(v.text.toLowerCase())),
      onSelected: onChanged,
      fieldViewBuilder: (context, controller, focusNode, _) => TextField(
        controller: controller,
        focusNode: focusNode,
        onChanged: onChanged,
        decoration: const InputDecoration(
          labelText: 'Tipo',
        ),
      ),
    );
  }
}
'''

target_path = r'E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\views\zeepub_volume_edit_view.dart'
with open(target_path, 'w', encoding='utf-8') as f:
    f.write(edit_view_code)

print('Updated zeepub_volume_edit_view.dart successfully')
