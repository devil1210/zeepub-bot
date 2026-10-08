# -*- coding: utf-8 -*-
import os

# 1. Update zeepub_volume_edit_view.dart
v_path = r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\views\zeepub_volume_edit_view.dart"
with open(v_path, 'r', encoding='utf-8') as f:
    v_content = f.read()

# Update constructor
old_ctor = '''class ZeepubVolumeEditView extends StatefulWidget {
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
  });'''

new_ctor = '''class ZeepubVolumeEditView extends StatefulWidget {
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
  });'''

v_content = v_content.replace(old_ctor, new_ctor)

# Add title selection handlers right after _onSeriesSelected
old_series_handler = '''    setState(() {
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
  }'''

new_series_and_title_handlers = '''    setState(() {
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
  }'''

v_content = v_content.replace(old_series_handler, new_series_and_title_handlers)

# Replace Title text fields with Autocomplete widgets
old_title_fields = '''                        AppTextField(
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
                        ),'''

# Note: handle both UTF-8 accented and unaccented matches in existing file
if 'T\u00edtulo en ingl\u00e9s / principal' in v_content or 'Título en inglés / principal' in v_content:
    pass

# Let's find the exact block around line 668 in v_content
target_anchor = "label: 'T"
target_end_anchor = "value: _titleSort,"

import re
pattern = re.compile(r"AppTextField\(\s+label:\s*'T[^\']*(?:tulo|ulo)\s+en\s+ingl[^\']*s\s*/\s*principal'.*?ResponsiveRow\(\s+children:\s*\[\s+AppTextField\(\s+label:\s*'T[^\']*(?:tulo|ulo)\s+en\s+espa[^\']*ol'.*?onChanged:\s*\(v\)\s*=>\s*setState\(\(\)\s*=>\s*_titleSpanish\s*=\s*v\),\s*\),", re.DOTALL)

replacement = '''Autocomplete<String>(
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
                                  decoration: const InputDecoration(
                                    labelText: 'Título en español',
                                    hintText: 'Título en español',
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
                            ),'''

v_content, count = pattern.subn(replacement, v_content)
print(f"Replaced title inputs count: {count}")

with open(v_path, 'w', encoding='utf-8') as f:
    f.write(v_content)
print("Updated zeepub_volume_edit_view.dart with Title Autocomplete")

# 2. Update zeepub_editorial_view.dart to pass volumes
e_path = r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\views\zeepub_editorial_view.dart"
with open(e_path, 'r', encoding='utf-8') as f:
    e_content = f.read()

old_edit_call = '''        if (state.activeVolume != null) {
          return ZeepubVolumeEditView(
            volume: state.activeVolume!,
            seriesList: state.seriesList,
            workgroups: state.workgroups,
            baseUrl: state.baseUrl,
            onBack: () => cubit.closeVolumeDetail(),
          );
        }'''

new_edit_call = '''        if (state.activeVolume != null) {
          return ZeepubVolumeEditView(
            volume: state.activeVolume!,
            volumes: state.volumes,
            seriesList: state.seriesList,
            workgroups: state.workgroups,
            baseUrl: state.baseUrl,
            onBack: () => cubit.closeVolumeDetail(),
          );
        }'''

e_content = e_content.replace(old_edit_call, new_edit_call)
with open(e_path, 'w', encoding='utf-8') as f:
    f.write(e_content)
print("Updated zeepub_editorial_view.dart to pass volumes")
