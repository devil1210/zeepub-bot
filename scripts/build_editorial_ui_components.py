# -*- coding: utf-8 -*-
import os

base_dir = r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial"
views_dir = os.path.join(base_dir, "presentation", "views")
widgets_dir = os.path.join(views_dir, "widgets")

# 1. Telegram Simulator
simulator_code = '''import 'package:flutter/material.dart';

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

    final serieEng = v?.englishTitle.isNotEmpty == true
        ? v!.englishTitle
        : (s?.seriesEnglish.isNotEmpty == true ? s!.seriesEnglish : (s?.name ?? 'The Hidden Dungeon Only I Can Enter'));
    final serieSpa = v?.spanishTitle.isNotEmpty == true
        ? v!.spanishTitle
        : (s?.seriesSpanish.isNotEmpty == true ? s!.seriesSpanish : 'El calabozo oculto en el que solo yo puedo entrar');
    final serieRom = s?.name.isNotEmpty == true ? s!.name : 'Ore dake Haireru Kakushi Dungeon';
    final volNum = v?.volume != null ? (v!.volume! % 1 == 0 ? v.volume!.toInt().toString() : v.volume!.toString()) : '1.0';
    final autor = v?.author.isNotEmpty == true ? v!.author : (s?.author.isNotEmpty == true ? s!.author : 'Meguru Seto');
    final ilustrador = v?.illustrator.isNotEmpty == true ? v!.illustrator : (s?.illustrator.isNotEmpty == true ? s!.illustrator : 'Note Takehana');
    final traductor = v?.translator.isNotEmpty == true ? v!.translator : 'Hitsugaya Rin';
    final layoutBy = v?.layoutBy.isNotEmpty == true ? v!.layoutBy : 'ZeePubs';
    final editorial = v?.publisher.isNotEmpty == true ? v!.publisher : (s?.publisher.isNotEmpty == true ? s!.publisher : "God's Earth Translations");
    final sinopsis = v?.description.isNotEmpty == true
        ? v!.description!
        : (s?.description != null && s!.description!.isNotEmpty
            ? s.description!
            : 'Noir, el tercer hijo de un "noble mendigo", perdió su trabajo y el rumbo de su vida, pero la fortuna golpeó justo cuando estaba contemplando convertirse en aventurero...');
    final demography = v?.colorMode == 'color' ? 'Shounen' : 'Seinen';
    final genres = _formatGenres('#Romance #Sobrenatural #Comedia #Ecchi #Accion #Aventura #Fantasia');
    final slug = s?.slug.isNotEmpty == true ? s!.slug : 'Ore_Dake_Haireru_Kakushi_Dungeon';
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
    final defaultTpl = '{?series_english}<b>[EN] {series_english}</b>{/?}\n'
        '{?romaji_title}<b>[JA] {romaji_title}</b>{/?}\n'
        '{?series_spanish}<b>[ES] {series_spanish}</b>{/?}\n'
        '<b>Volumen {volumen}</b>\n'
        '{genres}\n\n'
        'Ficha Tecnica:\n'
        '• Autor: {autor}\n'
        '• Ilustrador: {illustrator}\n'
        '• Traductor: {traductor}\n'
        '• Editorial: {editorial}\n\n'
        'Sinopsis:\n{sinopsis}\n\n'
        '#{slug}';

    final tpl = widget.templateContent.trim().isNotEmpty ? widget.templateContent : defaultTpl;
    final evaluatedRaw = _interpolate(tpl);
    final charCount = evaluatedRaw.length;
    final channelName = widget.channel?.name.isNotEmpty == true ? widget.channel!.name : 'Canal Oficial ZeePub';
    final v = widget.volume;
    final s = widget.series;
    final coverUrl = widget.customCoverUrl ?? v?.coverUrl ?? s?.coverUrl ?? '';

    final serieEng = v?.englishTitle.isNotEmpty == true
        ? v!.englishTitle
        : (s?.seriesEnglish.isNotEmpty == true ? s!.seriesEnglish : (s?.name ?? 'The Hidden Dungeon Only I Can Enter'));
    final serieSpa = v?.spanishTitle.isNotEmpty == true
        ? v!.spanishTitle
        : (s?.seriesSpanish.isNotEmpty == true ? s!.seriesSpanish : 'El calabozo oculto en el que solo yo puedo entrar');
    final serieRom = s?.name.isNotEmpty == true ? s!.name : 'Ore dake Haireru Kakushi Dungeon';
    final volNum = v?.volume != null ? (v!.volume! % 1 == 0 ? v.volume!.toInt().toString() : v.volume!.toString()) : '1';
    final autor = v?.author.isNotEmpty == true ? v!.author : (s?.author.isNotEmpty == true ? s!.author : 'Meguru Seto');
    final ilustrador = v?.illustrator.isNotEmpty == true ? v!.illustrator : (s?.illustrator.isNotEmpty == true ? s!.illustrator : 'Note Takehana');
    final traductor = v?.translator.isNotEmpty == true ? v!.translator : 'Hitsugaya Rin';
    final editorial = v?.publisher.isNotEmpty == true ? v!.publisher : (s?.publisher.isNotEmpty == true ? s!.publisher : "God's Earth Translations");
    final sinopsis = v?.description.isNotEmpty == true
        ? v!.description!
        : (s?.description != null && s!.description!.isNotEmpty
            ? s.description!
            : 'Noir, el tercer hijo de un "noble mendigo", perdió su trabajo y el rumbo de su vida...');
    final genres = _formatGenres('#Romance #Sobrenatural #Comedia #Ecchi #Accion #Aventura #Fantasia');
    final slug = s?.slug.isNotEmpty == true ? s!.slug : 'Ore_Dake_Haireru_Kakushi_Dungeon';

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
                                'canal de difusion',
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
                                        const Text('Ficha Tecnica', style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold)),
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
                                        _fieldRow('Categoria', 'Novela Ligera'),
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
                                        const Text('Ver Sinopsis', style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold)),
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
'''

# 2. Templates Tab
templates_tab_code = '''import 'package:flutter/material.dart';
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
    final newText = text.replaceRange(
      selection.start >= 0 ? selection.start : text.length,
      selection.end >= 0 ? selection.end : text.length,
      tag,
    );
    _contentController.value = TextEditingValue(
      text: newText,
      selection: TextSelection.collapsed(
        offset: (selection.start >= 0 ? selection.start : text.length) + tag.length,
      ),
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
                            tpl.isDefault ? Icons.star_rounded : (tpl.platform == 'facebook' ? Icons.facebook : Icons.telegram),
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
                          value: _platform,
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
                      hintText: 'Escribe el codigo HTML enriquecido o plantilla...',
                    ),
                  ),
                  const SizedBox(height: 16),

                  Row(
                    children: [
                      if (_selectedTemplate?.id != null)
                        OutlinedButton.icon(
                          icon: const Icon(Icons.delete_outline, size: 18, color: Colors.red),
                          label: const Text('Eliminar Plantilla', style: TextStyle(color: Colors.red)),
                          onPressed: () => cubit.deleteTemplate(_selectedTemplate!.id!),
                        ),
                      const Spacer(),
                      FilledButton.icon(
                        icon: const Icon(Icons.save_rounded, size: 18),
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

            // RIGHT: Live Telegram Simulator Preview
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

  Widget _formatButton(String label, VoidCallback onTap) {
    return OutlinedButton(
      style: OutlinedButton.styleFrom(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        minimumSize: Size.zero,
        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
      ),
      onPressed: onTap,
      child: Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
    );
  }
}
'''

# 3. Workgroups Tab
workgroups_tab_code = '''import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '/features/zeepub_editorial/presentation/cubit/zeepub_editorial_cubit.dart';
import '/features/zeepub_editorial/presentation/cubit/zeepub_editorial_state.dart';

class ZeepubWorkgroupsTab extends StatefulWidget {
  const ZeepubWorkgroupsTab({super.key});

  @override
  State<ZeepubWorkgroupsTab> createState() => _ZeepubWorkgroupsTabState();
}

class _ZeepubWorkgroupsTabState extends State<ZeepubWorkgroupsTab> {
  String _searchQuery = '';

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final tt = Theme.of(context).textTheme;

    return BlocBuilder<ZeepubEditorialCubit, ZeepubEditorialState>(
      builder: (context, state) {
        final groups = state.workgroups.where((g) {
          if (_searchQuery.isEmpty) return true;
          final q = _searchQuery.toLowerCase();
          return g.name.toLowerCase().contains(q) || g.siglas.toLowerCase().contains(q);
        }).toList();

        return Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      decoration: const InputDecoration(
                        prefixIcon: Icon(Icons.search),
                        hintText: 'Buscar por nombre de fansub o siglas...',
                      ),
                      onChanged: (v) => setState(() => _searchQuery = v.trim()),
                    ),
                  ),
                  const SizedBox(width: 12),
                  FilledButton.icon(
                    icon: const Icon(Icons.refresh),
                    label: const Text('Recargar'),
                    onPressed: () => context.read<ZeepubEditorialCubit>().init(),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Expanded(
                child: groups.isEmpty
                    ? const Center(child: Text('No se encontraron fansubs registrados.'))
                    : GridView.builder(
                        gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
                          maxCrossAxisExtent: 360,
                          mainAxisSpacing: 12,
                          crossAxisSpacing: 12,
                          mainAxisExtent: 170,
                        ),
                        itemCount: groups.length,
                        itemBuilder: (context, idx) {
                          final g = groups[idx];
                          return Card.outlined(
                            child: Padding(
                              padding: const EdgeInsets.all(12),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      CircleAvatar(
                                        backgroundColor: cs.primaryContainer,
                                        child: Text(
                                          g.siglas.isNotEmpty ? g.siglas : (g.name.isNotEmpty ? g.name[0] : 'G'),
                                          style: TextStyle(fontWeight: FontWeight.bold, color: cs.onPrimaryContainer),
                                        ),
                                      ),
                                      const SizedBox(width: 10),
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            Text(g.name, style: tt.titleSmall?.copyWith(fontWeight: FontWeight.bold), maxLines: 1, overflow: TextOverflow.ellipsis),
                                            if (g.siglas.isNotEmpty)
                                              Text('Siglas: [${g.siglas}]', style: tt.labelSmall?.copyWith(color: cs.onSurfaceVariant)),
                                          ],
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  Expanded(
                                    child: Text(
                                      g.description.isNotEmpty ? g.description : 'Grupo traductor oficial registrado en ZeePub.',
                                      style: tt.bodySmall?.copyWith(color: cs.onSurfaceVariant),
                                      maxLines: 3,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                  if (g.websiteUrl != null && g.websiteUrl!.isNotEmpty)
                                    Text(
                                      g.websiteUrl!,
                                      style: tt.labelSmall?.copyWith(color: Colors.blue),
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
              ),
            ],
          ),
        );
      },
    );
  }
}
'''

# 4. Calendar Tab
calendar_tab_code = '''import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '/features/zeepub_editorial/presentation/cubit/zeepub_editorial_cubit.dart';
import '/features/zeepub_editorial/presentation/cubit/zeepub_editorial_state.dart';

class ZeepubCalendarTab extends StatelessWidget {
  const ZeepubCalendarTab({super.key});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final tt = Theme.of(context).textTheme;

    return BlocBuilder<ZeepubEditorialCubit, ZeepubEditorialState>(
      builder: (context, state) {
        final cubit = context.read<ZeepubEditorialCubit>();
        final queue = state.queue;

        return Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  const Icon(Icons.calendar_month_rounded),
                  const SizedBox(width: 8),
                  Text('AGENDA DE PUBLICACIONES PROGRAMADAS', style: tt.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                  const Spacer(),
                  FilledButton.icon(
                    icon: const Icon(Icons.refresh),
                    label: const Text('Actualizar'),
                    onPressed: () => cubit.loadQueue(),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Expanded(
                child: queue.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.event_available_rounded, size: 48, color: cs.onSurfaceVariant),
                            const SizedBox(height: 12),
                            const Text('No hay publicaciones pendientes o en cola.'),
                          ],
                        ),
                      )
                    : ListView.builder(
                        itemCount: queue.length,
                        itemBuilder: (context, idx) {
                          final item = queue[idx];
                          final isError = item.status == 'failed' || item.status == 'error';
                          return Card.outlined(
                            margin: const EdgeInsets.only(bottom: 8),
                            child: ListTile(
                              leading: item.coverUrl != null && item.coverUrl!.isNotEmpty
                                  ? ClipRRect(
                                      borderRadius: BorderRadius.circular(4),
                                      child: Image.network(
                                        item.coverUrl!.startsWith('http') ? item.coverUrl! : '${state.baseUrl}${item.coverUrl!}',
                                        width: 36,
                                        height: 48,
                                        fit: BoxFit.cover,
                                        errorBuilder: (_, _, _) => const Icon(Icons.book, size: 24),
                                      ),
                                    )
                                  : const Icon(Icons.book, size: 36),
                              title: Text(item.series ?? item.bookHash, style: const TextStyle(fontWeight: FontWeight.bold)),
                              subtitle: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('Canal: ${item.channel ?? "Telegram"} · Fecha: ${item.scheduledFor ?? "Inmediato"}'),
                                  if (item.error != null)
                                    Text('Error: ${item.error}', style: const TextStyle(color: Colors.red, fontSize: 11)),
                                ],
                              ),
                              trailing: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                    decoration: BoxDecoration(
                                      color: isError ? Colors.red.withValues(alpha: 0.2) : Colors.blue.withValues(alpha: 0.2),
                                      borderRadius: BorderRadius.circular(6),
                                    ),
                                    child: Text(
                                      item.status.toUpperCase(),
                                      style: TextStyle(
                                        fontSize: 10,
                                        fontWeight: FontWeight.bold,
                                        color: isError ? Colors.red : Colors.blue,
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  if (isError)
                                    IconButton(
                                      icon: const Icon(Icons.replay_rounded, size: 20),
                                      tooltip: 'Reintentar',
                                      onPressed: () => cubit.retryQueueItem(item.id),
                                    ),
                                  IconButton(
                                    icon: const Icon(Icons.cancel_outlined, size: 20, color: Colors.red),
                                    tooltip: 'Cancelar',
                                    onPressed: () => cubit.cancelQueueItem(item.id),
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
              ),
            ],
          ),
        );
      },
    );
  }
}
'''

# 5. Posts Tab
posts_tab_code = '''import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '/features/zeepub_editorial/presentation/cubit/zeepub_editorial_cubit.dart';
import '/features/zeepub_editorial/presentation/cubit/zeepub_editorial_state.dart';

class ZeepubPostsTab extends StatelessWidget {
  const ZeepubPostsTab({super.key});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final tt = Theme.of(context).textTheme;

    return BlocBuilder<ZeepubEditorialCubit, ZeepubEditorialState>(
      builder: (context, state) {
        final cubit = context.read<ZeepubEditorialCubit>();
        final posts = state.posts;

        return Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  const Icon(Icons.history_rounded),
                  const SizedBox(width: 8),
                  Text('HISTORIAL DE PUBLICACIONES ENVIADAS', style: tt.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                  const Spacer(),
                  FilledButton.icon(
                    icon: const Icon(Icons.refresh),
                    label: const Text('Actualizar'),
                    onPressed: () => cubit.loadPosts(),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Expanded(
                child: posts.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.mark_chat_read_rounded, size: 48, color: cs.onSurfaceVariant),
                            const SizedBox(height: 12),
                            const Text('No hay publicaciones registradas en el historial.'),
                          ],
                        ),
                      )
                    : ListView.builder(
                        itemCount: posts.length,
                        itemBuilder: (context, idx) {
                          final post = posts[idx];
                          return Card.outlined(
                            margin: const EdgeInsets.only(bottom: 8),
                            child: ListTile(
                              leading: post.coverUrl != null && post.coverUrl!.isNotEmpty
                                  ? ClipRRect(
                                      borderRadius: BorderRadius.circular(4),
                                      child: Image.network(
                                        post.coverUrl!.startsWith('http') ? post.coverUrl! : '${state.baseUrl}${post.coverUrl!}',
                                        width: 36,
                                        height: 48,
                                        fit: BoxFit.cover,
                                        errorBuilder: (_, _, _) => const Icon(Icons.book, size: 24),
                                      ),
                                    )
                                  : const Icon(Icons.book, size: 36),
                              title: Text(post.series ?? post.title ?? post.bookHash, style: const TextStyle(fontWeight: FontWeight.bold)),
                              subtitle: Text('Canal: ${post.channel ?? "Telegram"} · Publicado: ${post.publishedAt ?? "Reciente"}'),
                              trailing: post.postUrl != null && post.postUrl!.isNotEmpty
                                  ? IconButton(
                                      icon: const Icon(Icons.open_in_new_rounded, size: 18),
                                      tooltip: 'Ver Post',
                                      onPressed: () {},
                                    )
                                  : null,
                            ),
                          );
                        },
                      ),
              ),
            ],
          ),
        );
      },
    );
  }
}
'''

# 6. Publisher View
publisher_view_code = '''import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '/features/zeepub_editorial/data/models/zeepub_channel.dart';
import '/features/zeepub_editorial/data/models/zeepub_template.dart';
import '/features/zeepub_editorial/data/models/zeepub_volume.dart';
import '/features/zeepub_editorial/presentation/cubit/zeepub_editorial_cubit.dart';
import '/features/zeepub_editorial/presentation/cubit/zeepub_editorial_state.dart';
import 'widgets/telegram_simulator.dart';

class ZeepubPublisherView extends StatefulWidget {
  final ZeepubVolume volume;
  final VoidCallback onBack;

  const ZeepubPublisherView({
    super.key,
    required this.volume,
    required this.onBack,
  });

  @override
  State<ZeepubPublisherView> createState() => _ZeepubPublisherViewState();
}

class _ZeepubPublisherViewState extends State<ZeepubPublisherView> with SingleTickerProviderStateMixin {
  late final TabController _modeTabController;
  late final TextEditingController _captionController;

  ZeepubChannel? _selectedChannel;
  ZeepubTemplate? _selectedTemplate;
  bool _sendAsFile = true;
  DateTime _scheduledDate = DateTime.now().add(const Duration(hours: 1));
  TimeOfDay _scheduledTime = const TimeOfDay(hour: 12, minute: 0);

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
    '{slug}',
  ];

  @override
  void initState() {
    super.initState();
    _modeTabController = TabController(length: 2, vsync: this);
    _captionController = TextEditingController();
  }

  @override
  void dispose() {
    _modeTabController.dispose();
    _captionController.dispose();
    super.dispose();
  }

  void _insertTag(String tag) {
    final text = _captionController.text;
    final selection = _captionController.selection;
    final newText = text.replaceRange(
      selection.start >= 0 ? selection.start : text.length,
      selection.end >= 0 ? selection.end : text.length,
      tag,
    );
    _captionController.value = TextEditingValue(
      text: newText,
      selection: TextSelection.collapsed(
        offset: (selection.start >= 0 ? selection.start : text.length) + tag.length,
      ),
    );
    setState(() {});
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _scheduledDate,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (picked != null) {
      setState(() => _scheduledDate = picked);
    }
  }

  Future<void> _pickTime() async {
    final picked = await showTimePicker(
      context: context,
      initialTime: _scheduledTime,
    );
    if (picked != null) {
      setState(() => _scheduledTime = picked);
    }
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final tt = Theme.of(context).textTheme;

    return BlocBuilder<ZeepubEditorialCubit, ZeepubEditorialState>(
      builder: (context, state) {
        final cubit = context.read<ZeepubEditorialCubit>();
        final channels = state.channels;
        final templates = state.templates;

        if (channels.isNotEmpty && _selectedChannel == null) {
          _selectedChannel = channels.where((c) => c.isFavorite).firstOrNull ?? channels.first;
        }
        if (templates.isNotEmpty && _selectedTemplate == null) {
          _selectedTemplate = templates.where((t) => t.isDefault).firstOrNull ?? templates.first;
          if (_captionController.text.isEmpty && _selectedTemplate != null) {
            _captionController.text = _selectedTemplate!.content;
          }
        }

        final volTitle = widget.volume.spanishTitle.isNotEmpty
            ? widget.volume.spanishTitle
            : (widget.volume.seriesName ?? widget.volume.title);

        return Scaffold(
          appBar: AppBar(
            leading: IconButton(
              icon: const Icon(Icons.arrow_back),
              tooltip: 'Volver',
              onPressed: widget.onBack,
            ),
            title: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Publicador en Canal de Telegram', style: tt.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                Text(
                  '$volTitle ${widget.volume.volume != null ? "· Vol. ${widget.volume.volume}" : ""}',
                  style: tt.bodySmall?.copyWith(color: cs.onSurfaceVariant),
                ),
              ],
            ),
            actions: [
              TextButton(
                onPressed: widget.onBack,
                child: const Text('Cancelar'),
              ),
              const SizedBox(width: 8),
              FilledButton.icon(
                icon: const Icon(Icons.send_rounded, size: 18),
                label: Text(_modeTabController.index == 0 ? 'Publicar Inmediatamente' : 'Programar Publicacion'),
                style: FilledButton.styleFrom(backgroundColor: Colors.blue.shade700, foregroundColor: Colors.white),
                onPressed: state.saving
                    ? null
                    : () {
                        final customCaption = _captionController.text.trim().isNotEmpty ? _captionController.text.trim() : null;
                        if (_modeTabController.index == 0) {
                          cubit.publishNow(
                            bookHash: widget.volume.bookHash,
                            channelId: _selectedChannel?.id,
                            templateId: _selectedTemplate?.id,
                            customCaption: customCaption,
                            sendAsFile: _sendAsFile,
                          );
                        } else {
                          final fullDate = DateTime(
                            _scheduledDate.year,
                            _scheduledDate.month,
                            _scheduledDate.day,
                            _scheduledTime.hour,
                            _scheduledTime.minute,
                          );
                          cubit.schedulePublication(
                            bookHash: widget.volume.bookHash,
                            scheduledAtIso: fullDate.toUtc().toIso8601String(),
                            channelId: _selectedChannel?.id,
                            templateId: _selectedTemplate?.id,
                            customCaption: customCaption,
                            sendAsFile: _sendAsFile,
                          );
                        }
                      },
              ),
              const SizedBox(width: 16),
            ],
          ),
          body: Row(
            children: [
              // LEFT PANEL: Controls, Channel, Template, Caption
              Expanded(
                flex: 5,
                child: ListView(
                  padding: const EdgeInsets.all(20),
                  children: [
                    // Mode Selector Tabs
                    TabBar(
                      controller: _modeTabController,
                      onTap: (_) => setState(() {}),
                      tabs: const [
                        Tab(icon: Icon(Icons.bolt_rounded, size: 18), text: 'Publicar Ahora'),
                        Tab(icon: Icon(Icons.schedule_rounded, size: 18), text: 'Programar Fecha y Hora'),
                      ],
                    ),
                    const SizedBox(height: 16),

                    // Channel selector
                    DropdownButtonFormField<ZeepubChannel>(
                      value: _selectedChannel,
                      decoration: const InputDecoration(
                        labelText: 'Canal de Telegram Destino',
                        prefixIcon: Icon(Icons.cell_tower_rounded),
                      ),
                      items: [
                        for (final c in channels)
                          DropdownMenuItem(
                            value: c,
                            child: Text('${c.name} (${c.targetId})'),
                          ),
                      ],
                      onChanged: (v) => setState(() => _selectedChannel = v),
                    ),
                    const SizedBox(height: 12),

                    // Template selector
                    DropdownButtonFormField<ZeepubTemplate>(
                      value: _selectedTemplate,
                      decoration: const InputDecoration(
                        labelText: 'Plantilla de Publicacion',
                        prefixIcon: Icon(Icons.layout_template),
                      ),
                      items: [
                        for (final t in templates)
                          DropdownMenuItem(
                            value: t,
                            child: Text('${t.isDefault ? "[Oficial] " : ""}${t.name}'),
                          ),
                      ],
                      onChanged: (v) {
                        if (v != null) {
                          setState(() {
                            _selectedTemplate = v;
                            _captionController.text = v.content;
                          });
                        }
                      },
                    ),
                    const SizedBox(height: 12),

                    // If Schedule Mode: Date & Time pickers
                    if (_modeTabController.index == 1) ...[
                      Row(
                        children: [
                          Expanded(
                            child: OutlinedButton.icon(
                              icon: const Icon(Icons.calendar_today, size: 16),
                              label: Text('${_scheduledDate.year}-${_scheduledDate.month.toString().padLeft(2, "0")}-${_scheduledDate.day.toString().padLeft(2, "0")}'),
                              onPressed: _pickDate,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: OutlinedButton.icon(
                              icon: const Icon(Icons.access_time, size: 16),
                              label: Text('${_scheduledTime.hour.toString().padLeft(2, "0")}:${_scheduledTime.minute.toString().padLeft(2, "0")}'),
                              onPressed: _pickTime,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                    ],

                    SwitchListTile(
                      title: const Text('Enviar Archivo EPUB Adjunto'),
                      subtitle: const Text('Si se desactiva, solo se enviara el anuncio con la portada.'),
                      value: _sendAsFile,
                      onChanged: (v) => setState(() => _sendAsFile = v),
                    ),
                    const SizedBox(height: 12),

                    // Caption Editor
                    Text('Mensaje / Caption Personalizado', style: tt.labelLarge),
                    const SizedBox(height: 6),
                    Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      children: [
                        for (final v in _variables)
                          ActionChip(
                            label: Text(v, style: const TextStyle(fontSize: 10, fontFamily: 'monospace')),
                            padding: EdgeInsets.zero,
                            onPressed: () => _insertTag(v),
                          ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: _captionController,
                      maxLines: 12,
                      onChanged: (_) => setState(() {}),
                      style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
                      decoration: const InputDecoration(
                        border: OutlineInputBorder(),
                        hintText: 'Plantilla de mensaje...',
                      ),
                    ),
                  ],
                ),
              ),

              // RIGHT PANEL: Live Telegram Simulator
              Expanded(
                flex: 5,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: TelegramSimulator(
                    templateContent: _captionController.text,
                    volume: widget.volume,
                    channel: _selectedChannel,
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
}
'''

# 7. Editorial Main View
editorial_view_code = '''import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '/features/zeepub_editorial/data/models/zeepub_volume.dart';
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
    final urlCtrl = TextEditingController(text: currentUrl);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.dns_rounded),
            SizedBox(width: 8),
            Text('Conexion con ZeePub Bot'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Ingresa la URL del backend de ZeePub (local o VPS).',
              style: TextStyle(fontSize: 13),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: urlCtrl,
              decoration: const InputDecoration(
                labelText: 'URL Base del Servidor',
                hintText: 'http://localhost:8001 o https://zeepubs.com',
                prefixIcon: Icon(Icons.link),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () {
              final newUrl = urlCtrl.text.trim();
              if (newUrl.isNotEmpty) {
                context.read<ZeepubEditorialCubit>().updateBaseUrl(newUrl);
              }
              Navigator.of(ctx).pop();
            },
            child: const Text('Guardar y Reconectar'),
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
      listener: (BuildContext context, ZeepubEditorialState state) {
        if (state.errorMessage != null) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              backgroundColor: cs.error,
              content: Text(state.errorMessage!),
            ),
          );
          context.read<ZeepubEditorialCubit>().clearNotifications();
        } else if (state.successMessage != null) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              backgroundColor: Colors.green.shade700,
              content: Text(state.successMessage!),
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
                  icon: const Icon(Icons.layout_template, size: 18),
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
                    hintText: 'Buscar por titulo, serie, autor o traductor...',
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
'''

with open(os.path.join(widgets_dir, "telegram_simulator.dart"), "w", encoding="utf-8") as f:
    f.write(simulator_code)
with open(os.path.join(widgets_dir, "templates_tab.dart"), "w", encoding="utf-8") as f:
    f.write(templates_tab_code)
with open(os.path.join(widgets_dir, "workgroups_tab.dart"), "w", encoding="utf-8") as f:
    f.write(workgroups_tab_code)
with open(os.path.join(widgets_dir, "calendar_tab.dart"), "w", encoding="utf-8") as f:
    f.write(calendar_tab_code)
with open(os.path.join(widgets_dir, "posts_tab.dart"), "w", encoding="utf-8") as f:
    f.write(posts_tab_code)
with open(os.path.join(views_dir, "zeepub_publisher_view.dart"), "w", encoding="utf-8") as f:
    f.write(publisher_view_code)
with open(os.path.join(views_dir, "zeepub_editorial_view.dart"), "w", encoding="utf-8") as f:
    f.write(editorial_view_code)

print("Generated all Editorial UI components and tabs successfully")
