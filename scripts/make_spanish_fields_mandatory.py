# -*- coding: utf-8 -*-
import io, os, re, sys

# 1. Update zeepub_volume_edit_view.dart
v_path = r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\views\zeepub_volume_edit_view.dart"
with open(v_path, 'r', encoding='utf-8') as f:
    v_content = f.read()

# Add validation check in _handleSave
old_handle_save = '''  Future<void> _handleSave() async {
    final cubit = context.read<ZeepubEditorialCubit>();'''

new_handle_save = '''  Future<void> _handleSave() async {
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

    final cubit = context.read<ZeepubEditorialCubit>();'''

v_content = v_content.replace(old_handle_save, new_handle_save)

# Update Serie en español with errorText / error: 'Obligatorio' and Autocomplete
old_series_spa = '''                              AppTextField(
                                label: 'Serie en español',
                                value: _seriesSpanish,
                                hint: 'Nombre de la serie en español',
                                onChanged: (v) => setState(() => _seriesSpanish = v),
                              ),'''

new_series_spa = '''                              Autocomplete<String>(
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
                              ),'''

v_content = v_content.replace(old_series_spa, new_series_spa)

# Update Título en español with errorText: 'Obligatorio'
old_title_spa = '''                            Autocomplete<String>(
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

new_title_spa = '''                            Autocomplete<String>(
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
                            ),'''

v_content = v_content.replace(old_title_spa, new_title_spa)

with open(v_path, 'w', encoding='utf-8') as f:
    f.write(v_content)
print("Updated zeepub_volume_edit_view.dart with Mandatory Spanish Fields")

# 2. Update volume_edit_dialog.dart with Mandatory Spanish Title validation
d_path = r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\views\widgets\volume_edit_dialog.dart"
with open(d_path, 'r', encoding='utf-8') as f:
    d_content = f.read()

old_d_save = '''  Future<void> _handleSave() async {
    final cubit = context.read<ZeepubEditorialCubit>();'''

new_d_save = '''  Future<void> _handleSave() async {
    if (_spanishTitleController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          backgroundColor: Colors.red,
          content: Text('El campo "Título en Español" es obligatorio'),
        ),
      );
      return;
    }

    final cubit = context.read<ZeepubEditorialCubit>();'''

d_content = d_content.replace(old_d_save, new_d_save)

old_d_spa_input = '''                                TextFormField(
                                  controller: _spanishTitleController,
                                  decoration: const InputDecoration(
                                    labelText: 'Título en Español (Oficial / Fansub)',
                                    border: OutlineInputBorder(),
                                    isDense: true,
                                  ),
                                ),'''

new_d_spa_input = '''                                TextFormField(
                                  controller: _spanishTitleController,
                                  onChanged: (_) => setState(() {}),
                                  decoration: InputDecoration(
                                    labelText: 'Título en Español (Oficial / Fansub)',
                                    border: const OutlineInputBorder(),
                                    isDense: true,
                                    errorText: _spanishTitleController.text.trim().isEmpty ? 'Obligatorio' : null,
                                  ),
                                ),'''

d_content = d_content.replace(old_d_spa_input, new_d_spa_input)

with open(d_path, 'w', encoding='utf-8') as f:
    f.write(d_content)
print("Updated volume_edit_dialog.dart with Mandatory Spanish Fields")
