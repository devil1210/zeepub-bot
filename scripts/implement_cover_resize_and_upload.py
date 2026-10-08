# -*- coding: utf-8 -*-
import os, re

# 1. Update api/routes/editorial_routes.py
backend_path = r"e:\Descargas\Zeepub-bot\api\routes\editorial_routes.py"
with open(backend_path, 'r', encoding='utf-8') as f:
    b_content = f.read()

# Add route registration
old_reg = '''            for sync_suffix in ["/sync_file", "/sync-file"]:
                self.router.add_api_route(
                    f"{prefix}/{{book_hash}}{sync_suffix}",
                    self.sync_volume_file,
                    methods=["POST", "GET"],
                    summary="Re-escanear metadatos directamente del archivo EPUB físico",
                )'''

new_reg = '''            for sync_suffix in ["/sync_file", "/sync-file"]:
                self.router.add_api_route(
                    f"{prefix}/{{book_hash}}{sync_suffix}",
                    self.sync_volume_file,
                    methods=["POST", "GET"],
                    summary="Re-escanear metadatos directamente del archivo EPUB físico",
                )
            self.router.add_api_route(
                f"{prefix}/{{book_hash}}/cover",
                self.upload_volume_cover,
                methods=["POST"],
                summary="Subir nueva portada de tomo",
            )'''

b_content = b_content.replace(old_reg, new_reg)

# Add method upload_volume_cover
old_method_anchor = '''    async def sync_volume_file(self, book_hash: str):'''

new_method = '''    async def upload_volume_cover(
        self,
        book_hash: str,
        file: UploadFile = File(...),
    ):
        """Sube una nueva portada personalizada para el tomo."""
        import hashlib
        from config.paths import COVERS_DIR
        from core.database import pg_manager
        from models.library import LocalBook
        from sqlalchemy import or_, select

        os.makedirs(COVERS_DIR, exist_ok=True)
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Archivo de imagen vacío")

        ext = os.path.splitext(file.filename or "")[1] or ".jpg"
        cover_filename = f"custom_{book_hash[:16]}_{hashlib.md5(content).hexdigest()[:8]}{ext}"
        cover_path = os.path.join(COVERS_DIR, cover_filename)
        with open(cover_path, "wb") as f:
            f.write(content)

        cover_url = f"/api/library/covers/{cover_filename}"

        async with pg_manager.get_session() as session:
            stmt = select(LocalBook).where(
                or_(LocalBook.book_hash == book_hash, LocalBook.id == book_hash)
            )
            res = await session.execute(stmt)
            b = res.scalar_one_or_none()
            if not b:
                raise HTTPException(status_code=404, detail="Tomo no encontrado")

            b.cover_original = cover_url
            b.cover_high = cover_url
            b.cover_medium = cover_url
            b.cover_low = cover_url
            await session.commit()
            await cache_manager.delete_book(b.id)

        return {
            "success": True,
            "message": "Portada actualizada correctamente",
            "cover_url": cover_url,
        }

    async def sync_volume_file(self, book_hash: str):'''

b_content = b_content.replace(old_method_anchor, new_method)

with open(backend_path, 'w', encoding='utf-8') as f:
    f.write(b_content)
print("Updated editorial_routes.py with cover upload endpoint")

# 2. Update zeepub_api_client.dart
api_client_path = r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\data\datasources\zeepub_api_client.dart"
with open(api_client_path, 'r', encoding='utf-8') as f:
    a_content = f.read()

# Add http import if needed or check if http is available
if 'uploadVolumeCover' not in a_content:
    old_end = '''  Future<Map<String, dynamic>> schedulePublication({'''
    upload_method = '''  Future<Map<String, dynamic>> uploadVolumeCover(String bookHash, List<int> fileBytes, String filename) async {
    final uri = Uri.parse('$baseUrl/api/editorial/volumes/$bookHash/cover');
    final request = http.MultipartRequest('POST', uri);
    request.files.add(http.MultipartFile.fromBytes('file', fileBytes, filename: filename));
    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    }
    throw Exception('Error al subir portada: ${response.statusCode} - ${response.body}');
  }

  Future<Map<String, dynamic>> schedulePublication({'''
    a_content = a_content.replace(old_end, upload_method)

with open(api_client_path, 'w', encoding='utf-8') as f:
    f.write(a_content)
print("Updated zeepub_api_client.dart with uploadVolumeCover")

# 3. Update zeepub_editorial_repository.dart
repo_path = r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\data\repositories\zeepub_editorial_repository.dart"
with open(repo_path, 'r', encoding='utf-8') as f:
    r_content = f.read()

if 'uploadVolumeCover' not in r_content:
    r_insert = '''  Future<String> uploadVolumeCover(String bookHash, List<int> fileBytes, String filename) async {
    final res = await _client.uploadVolumeCover(bookHash, fileBytes, filename);
    return res['cover_url']?.toString() ?? '';
  }

  Future<void> syncVolumeFile(String bookHash) => _client.syncVolumeFile(bookHash);'''
    r_content = r_content.replace('Future<void> syncVolumeFile(String bookHash) => _client.syncVolumeFile(bookHash);', r_insert)

with open(repo_path, 'w', encoding='utf-8') as f:
    f.write(r_content)
print("Updated zeepub_editorial_repository.dart with uploadVolumeCover")

# 4. Update zeepub_editorial_cubit.dart
cubit_path = r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\cubit\zeepub_editorial_cubit.dart"
with open(cubit_path, 'r', encoding='utf-8') as f:
    c_content = f.read()

if 'uploadCover' not in c_content:
    c_insert = '''  Future<String?> uploadCover(String bookHash, List<int> bytes, String filename) async {
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

  Future<void> syncVolumeFile(String bookHash) async {'''
    c_content = c_content.replace('Future<void> syncVolumeFile(String bookHash) async {', c_insert)

with open(cubit_path, 'w', encoding='utf-8') as f:
    f.write(c_content)
print("Updated zeepub_editorial_cubit.dart with uploadCover")

# 5. Update zeepub_volume_edit_view.dart with Resizable Left Sidebar + Cover Picker
v_path = r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\views\zeepub_volume_edit_view.dart"
with open(v_path, 'r', encoding='utf-8') as f:
    v_content = f.read()

# Add file_picker import
if "import 'package:file_picker/file_picker.dart';" not in v_content:
    v_content = "import 'package:file_picker/file_picker.dart';\n" + v_content

# Add _leftPanelWidth state variable and cover upload methods
old_state_init = '''class _ZeepubVolumeEditViewState extends State<ZeepubVolumeEditView> {
  // Identifiers'''

new_state_init = '''class _ZeepubVolumeEditViewState extends State<ZeepubVolumeEditView> {
  double _leftPanelWidth = 300.0;
  String? _customCoverUrl;

  // Identifiers'''

v_content = v_content.replace(old_state_init, new_state_init)

# Add _pickAndUploadCover and _showCustomUrlDialog methods
old_save_handler = '''  Future<void> _handleSave() async {'''

new_cover_methods = '''  Future<void> _pickAndUploadCover() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['jpg', 'jpeg', 'png', 'webp'],
      withData: true,
    );
    if (result != null && result.files.isNotEmpty) {
      final file = result.files.first;
      if (file.bytes != null) {
        final cubit = context.read<ZeepubEditorialCubit>();
        final newUrl = await cubit.uploadCover(widget.volume.bookHash, file.bytes!, file.name);
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

  Future<void> _handleSave() async {'''

v_content = v_content.replace(old_save_handler, new_cover_methods)

# Update _buildCoverUrl
old_build_cover = '''  String _buildCoverUrl() {
    if (widget.volume.coverUrl == null || widget.volume.coverUrl!.isEmpty) return '';
    if (widget.volume.coverUrl!.startsWith('http')) return widget.volume.coverUrl!;
    final cleanBase = widget.baseUrl.replaceAll(RegExp(r'/+$'), '');
    final cleanPath = widget.volume.coverUrl!.startsWith('/') ? widget.volume.coverUrl! : '/${widget.volume.coverUrl!}';
    return '$cleanBase$cleanPath';
  }'''

new_build_cover = '''  String _buildCoverUrl() {
    final rawCover = _customCoverUrl ?? widget.volume.coverUrl;
    if (rawCover == null || rawCover.isEmpty) return '';
    if (rawCover.startsWith('http')) return rawCover;
    final cleanBase = widget.baseUrl.replaceAll(RegExp(r'/+$'), '');
    final cleanPath = rawCover.startsWith('/') ? rawCover : '/$rawCover';
    return '$cleanBase$cleanPath';
  }'''

v_content = v_content.replace(old_build_cover, new_build_cover)

# Replace the left panel container and divider
pattern_left_panel = re.compile(r"// LEFT PANEL: Cover, File Info, Quick Actions\s+Container\(\s+width:\s*280,.*?// RIGHT PANEL:", re.DOTALL)

new_left_panel = '''// LEFT PANEL: Resizable Cover, File Info, Quick Actions
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

              // RIGHT PANEL:'''

v_content, count = pattern_left_panel.subn(new_left_panel, v_content)
print(f"Substituted left panel count: {count}")

with open(v_path, 'w', encoding='utf-8') as f:
    f.write(v_content)
print("Updated zeepub_volume_edit_view.dart with Resizable Left Sidebar and Cover Picker")
