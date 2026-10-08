# -*- coding: utf-8 -*-
import os, re

# 1. zeepub_api_client.dart
api_client_path = r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\data\datasources\zeepub_api_client.dart"
with open(api_client_path, 'r', encoding='utf-8') as f:
    a_content = f.read()

upload_method = '''  Future<Map<String, dynamic>> uploadVolumeCover(String bookHash, List<int> fileBytes, String filename) async {
    final uri = Uri.parse('$baseUrl/api/editorial/volumes/$bookHash/cover');
    final request = await _httpClient.postUrl(uri);
    final boundary = '----WebKitFormBoundary${DateTime.now().millisecondsSinceEpoch}';
    request.headers.set(HttpHeaders.contentTypeHeader, 'multipart/form-data; boundary=$boundary');

    request.write('--$boundary\\r\\n');
    request.write('Content-Disposition: form-data; name="file"; filename="$filename"\\r\\n');
    request.write('Content-Type: image/jpeg\\r\\n\\r\\n');
    request.add(fileBytes);
    request.write('\\r\\n--$boundary--\\r\\n');

    final response = await request.close();
    final responseBody = await response.transform(utf8.decoder).join();

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(responseBody) as Map<String, dynamic>;
    } else {
      throw HttpException('Error al subir portada HTTP ${response.statusCode}: $responseBody', uri: uri);
    }
  }
}'''

# Replace the closing brace with upload_method
if 'Future<Map<String, dynamic>> uploadVolumeCover' in a_content:
    # remove existing broken uploadVolumeCover
    a_content = re.sub(r'Future<Map<String, dynamic>> uploadVolumeCover.*?}\s*}', '}', a_content, flags=re.DOTALL)

a_content = re.sub(r'}\s*$', upload_method, a_content)

with open(api_client_path, 'w', encoding='utf-8') as f:
    f.write(a_content)
print("Updated zeepub_api_client.dart with pure HttpClient uploadVolumeCover")

# 2. zeepub_editorial_repository.dart
repo_path = r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\data\repositories\zeepub_editorial_repository.dart"
with open(repo_path, 'r', encoding='utf-8') as f:
    r_content = f.read()

if 'Future<String> uploadVolumeCover' not in r_content:
    r_insert = '''  Future<String> uploadVolumeCover(String bookHash, List<int> fileBytes, String filename) async {
    final res = await _client.uploadVolumeCover(bookHash, fileBytes, filename);
    return res['cover_url']?.toString() ?? '';
  }

  Future<void> syncVolumeFile(String bookHash) => _client.syncVolumeFile(bookHash);'''
    r_content = r_content.replace('Future<void> syncVolumeFile(String bookHash) => _client.syncVolumeFile(bookHash);', r_insert)

with open(repo_path, 'w', encoding='utf-8') as f:
    f.write(r_content)
print("Updated zeepub_editorial_repository.dart with uploadVolumeCover")

# 3. zeepub_editorial_cubit.dart
cubit_path = r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\cubit\zeepub_editorial_cubit.dart"
with open(cubit_path, 'r', encoding='utf-8') as f:
    c_content = f.read()

if 'Future<String?> uploadCover' not in c_content:
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

  Future<void> syncVolumeFromDisk(String bookHash) async {'''
    c_content = c_content.replace('Future<void> syncVolumeFromDisk(String bookHash) async {', c_insert)

with open(cubit_path, 'w', encoding='utf-8') as f:
    f.write(c_content)
print("Updated zeepub_editorial_cubit.dart with uploadCover")

# 4. zeepub_volume_edit_view.dart
v_path = r"E:\Descargas\ZeeTools\lib\features\zeepub_editorial\presentation\views\zeepub_volume_edit_view.dart"
with open(v_path, 'r', encoding='utf-8') as f:
    v_content = f.read()

# Fix FilePicker call and mounted context
old_pick_method = '''  Future<void> _pickAndUploadCover() async {
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
  }'''

new_pick_method = '''  Future<void> _pickAndUploadCover() async {
    final cubit = context.read<ZeepubEditorialCubit>();
    final files = await FilePicker.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['jpg', 'jpeg', 'png', 'webp'],
      dialogTitle: 'Seleccionar nueva portada para el tomo',
      withData: true,
      windowsOptions: const WindowsOptions(lockParentWindow: true),
    );
    if (files.isNotEmpty) {
      final file = files.first;
      if (file.bytes != null) {
        final newUrl = await cubit.uploadCover(widget.volume.bookHash, file.bytes!, file.name);
        if (newUrl != null && mounted) {
          setState(() {
            _customCoverUrl = newUrl;
          });
        }
      }
    }
  }'''

v_content = v_content.replace(old_pick_method, new_pick_method)

# Fix multiline string in filepath
v_content = re.sub(
    r"Text\(\s*'Ruta en Servidor:\s*\n\s*\$\{widget\.volume\.filepath\}'",
    r"Text('Ruta en Servidor: ${widget.volume.filepath ?? \"\"}'",
    v_content
)

with open(v_path, 'w', encoding='utf-8') as f:
    f.write(v_content)
print("Updated zeepub_volume_edit_view.dart with clean pickFiles and filepath")
