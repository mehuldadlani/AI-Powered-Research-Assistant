import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../models/paper_model.dart';
import '../../../../core/network/dio_client.dart';

part 'paper_remote_data_source.g.dart';

abstract class PaperRemoteDataSource {
  Future<List<PaperModel>> getPapers();
  Future<List<PaperModel>> searchPapers(String query);
}

class PaperRemoteDataSourceImpl implements PaperRemoteDataSource {
  final Dio dio;

  PaperRemoteDataSourceImpl(this.dio);

  @override
  Future<List<PaperModel>> getPapers() async {
    final response = await dio.get('/api/papers');
    return (response.data as List)
        .map((json) => PaperModel.fromJson(json))
        .toList();
  }

  @override
  Future<List<PaperModel>> searchPapers(String query) async {
    final response = await dio.get('/api/search_papers', queryParameters: {'query': query});
    return (response.data as List)
        .map((json) => PaperModel.fromJson(json))
        .toList();
  }
}

@riverpod
PaperRemoteDataSource paperRemoteDataSource(Ref ref) {
  final dio = ref.watch(dioClientProvider);
  return PaperRemoteDataSourceImpl(dio);
}