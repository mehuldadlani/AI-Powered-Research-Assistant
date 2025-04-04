import 'package:dartz/dartz.dart';
import '../../../../core/error/failures.dart';
import '../../domain/entities/paper.dart';
import '../../domain/repositories/paper_repository.dart';
import '../datasources/paper_remote_data_source.dart';

class PaperRepositoryImpl implements PaperRepository {
  final PaperRemoteDataSource remoteDataSource;

  PaperRepositoryImpl(this.remoteDataSource);

  @override
  Future<Either<Failure, List<Paper>>> getPapers() async {
    try {
      final paperModels = await remoteDataSource.getPapers();
      final papers = paperModels.map((model) => model.toEntity()).toList();
      return Right(papers);
    } catch (e) {
      return Left(ServerFailure());
    }
  }

  @override
  Future<Either<Failure, List<Paper>>> searchPapers(String query) async {
    try {
      final paperModels = await remoteDataSource.searchPapers(query);
      final papers = paperModels.map((model) => model.toEntity()).toList();
      return Right(papers);
    } catch (e) {
      return Left(ServerFailure());
    }
  }
}