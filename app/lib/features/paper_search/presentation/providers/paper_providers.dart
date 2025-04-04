import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../domain/entities/paper.dart';
import '../../domain/repositories/paper_repository.dart';
import '../../domain/usecases/get_papers.dart';
import '../../domain/usecases/search_papers.dart';
import '../../data/repositories/paper_repository_impl.dart';
import '../../data/datasources/paper_remote_data_source.dart';
import '../../../../core/usecases/usecase.dart';

part 'paper_providers.g.dart';

@riverpod
PaperRepository paperRepository(PaperRepositoryRef ref) {
  final remoteDataSource = ref.watch(paperRemoteDataSourceProvider);
  return PaperRepositoryImpl(remoteDataSource);
}

@riverpod
class Papers extends _$Papers {
  late final PaperRepository _repository;

  @override
  FutureOr<List<Paper>> build() async {
    _repository = ref.watch(paperRepositoryProvider);
    return _fetchPapers();
  }

  Future<List<Paper>> _fetchPapers() async {
    final usecase = GetPapers(_repository);
    final result = await usecase(NoParams());
    return result.fold(
      (failure) => throw Exception('Failed to fetch papers'),
      (papers) => papers,
    );
  }

  Future<void> searchPapers(String query) async {
    state = const AsyncValue.loading();
    final usecase = SearchPapers(_repository);
    final result = await usecase(query);
    state = result.fold(
      (failure) => AsyncValue.error(Exception('Failed to search papers'), StackTrace.current),
      AsyncValue.data,
    );
  }
}