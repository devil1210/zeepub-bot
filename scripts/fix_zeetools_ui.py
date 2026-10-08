import os

def fix_files():
    # 1. calendar_tab.dart
    p1 = r'E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\views\widgets\calendar_tab.dart'
    with open(p1, 'r', encoding='utf-8') as f:
        c1 = f.read()
    c1 = c1.replace(
        '      builder: (ctx) => StatefulBuilder(\n        builder: (context, setDlgState) {\n          return AlertDialog(',
        '      builder: (ctx) => StatefulBuilder(\n        builder: (context, setDlgState) {\n          final cs = Theme.of(context).colorScheme;\n          return AlertDialog('
    )
    c1 = c1.replace(
        '      builder: (context, state) {\n        final cubit = context.read<ZeepubEditorialCubit>();\n        final allItems = state.queue;',
        '      builder: (context, state) {\n        final cs = Theme.of(context).colorScheme;\n        final cubit = context.read<ZeepubEditorialCubit>();\n        final allItems = state.queue;'
    )
    with open(p1, 'w', encoding='utf-8') as f:
        f.write(c1)

    # 2. series_detail_view.dart
    p2 = r'E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\views\widgets\series_detail_view.dart'
    with open(p2, 'r', encoding='utf-8') as f:
        c2 = f.read()
    c2 = c2.replace(
        '  Widget _buildVolumeGridCard(BuildContext context, ZeepubVolume vol, ZeepubSeries s, String baseUrl, ZeepubEditorialCubit cubit) {\n    final coverUrl = _buildCoverUrl(vol.coverUrl ?? s.coverUrl, baseUrl);',
        '  Widget _buildVolumeGridCard(BuildContext context, ZeepubVolume vol, ZeepubSeries s, String baseUrl, ZeepubEditorialCubit cubit) {\n    final cs = Theme.of(context).colorScheme;\n    final coverUrl = _buildCoverUrl(vol.coverUrl ?? s.coverUrl, baseUrl);'
    )
    c2 = c2.replace(
        '    Widget _buildVolumeGridCard(BuildContext context, ZeepubVolume vol, ZeepubSeries s, String baseUrl, ZeepubEditorialCubit cubit) {\n    final coverUrl = _buildCoverUrl(vol.coverUrl ?? s.coverUrl, baseUrl);',
        '  Widget _buildVolumeGridCard(BuildContext context, ZeepubVolume vol, ZeepubSeries s, String baseUrl, ZeepubEditorialCubit cubit) {\n    final cs = Theme.of(context).colorScheme;\n    final coverUrl = _buildCoverUrl(vol.coverUrl ?? s.coverUrl, baseUrl);'
    )
    c2 = c2.replace(
        '  Widget _buildVolumeListTile(BuildContext context, ZeepubVolume vol, ZeepubSeries s, String baseUrl, ZeepubEditorialCubit cubit) {\n    final coverUrl = _buildCoverUrl(vol.coverUrl, baseUrl);',
        '  Widget _buildVolumeListTile(BuildContext context, ZeepubVolume vol, ZeepubSeries s, String baseUrl, ZeepubEditorialCubit cubit) {\n    final cs = Theme.of(context).colorScheme;\n    final coverUrl = _buildCoverUrl(vol.coverUrl, baseUrl);'
    )
    c2 = c2.replace(
        'errorBuilder: (_, __, ___) => const Icon(Icons.book, size: 20)',
        'errorBuilder: (_, _, _) => const Icon(Icons.book, size: 20)'
    )
    with open(p2, 'w', encoding='utf-8') as f:
        f.write(c2)

    # 3. workgroup_detail_view.dart
    p3 = r'E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\views\widgets\workgroup_detail_view.dart'
    with open(p3, 'r', encoding='utf-8') as f:
        c3 = f.read()
    c3 = c3.replace(
        '  Widget _buildAuditoriaTab(\n    BuildContext context,\n    ZeepubEditorialCubit cubit,\n    ZeepubWorkgroup group,\n    List<ZeepubAttachedBook> allBooks,\n    List<ZeepubAttachedBook> filteredBooks,\n    int badCount,\n    int goodCount,\n    int totalBooks,\n  ) {',
        '  Widget _buildAuditoriaTab(\n    BuildContext context,\n    ZeepubEditorialCubit cubit,\n    ZeepubWorkgroup group,\n    List<ZeepubAttachedBook> allBooks,\n    List<ZeepubAttachedBook> filteredBooks,\n    int badCount,\n    int goodCount,\n    int totalBooks,\n  ) {\n    final cs = Theme.of(context).colorScheme;'
    )
    with open(p3, 'w', encoding='utf-8') as f:
        f.write(c3)

    # 4. volume_detail_view.dart
    p4 = r'E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\views\widgets\volume_detail_view.dart'
    with open(p4, 'r', encoding='utf-8') as f:
        lines4 = f.readlines()
    for i, line in enumerate(lines4):
        if 's?.seriesEnglish.isNotEmpty == true' in line:
            lines4[i] = '        final seriesName = (s != null && s.seriesEnglish.isNotEmpty)\n'
            lines4[i+1] = '            ? s.seriesEnglish\n'
            lines4[i+2] = "            : (vol.seriesName.isNotEmpty ? vol.seriesName : 'Catálogo');\n"
        if '_buildSpecRow(\'IDIOMA\', vol.language' in line:
            lines4[i] = "                                                      _buildSpecRow('IDIOMA', vol.language.isNotEmpty ? vol.language : 'es'),\n"
    with open(p4, 'w', encoding='utf-8') as f:
        f.writelines(lines4)

    # 5. workgroups_tab.dart
    p5 = r'E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\views\widgets\workgroups_tab.dart'
    with open(p5, 'r', encoding='utf-8') as f:
        c5 = f.read()
    c5 = c5.replace("import '/features/zeepub_editorial/data/models/zeepub_workgroup.dart';\n", '')
    with open(p5, 'w', encoding='utf-8') as f:
        f.write(c5)

    # 6. zeepub_volume_edit_view.dart
    p6 = r'E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\views\zeepub_volume_edit_view.dart'
    with open(p6, 'r', encoding='utf-8') as f:
        c6 = f.read()
    c6 = c6.replace("    _series = v.seriesName ?? '';", "    _series = v.seriesName;")
    c6 = c6.replace("    _seriesEnglish = v.seriesName ?? '';", "    _seriesEnglish = v.seriesName;")
    with open(p6, 'w', encoding='utf-8') as f:
        f.write(c6)

    print('Applied all clean updates from script!')

if __name__ == '__main__':
    fix_files()
