import 'package:dartz/dartz.dart';
import '../../../../core/error/failures.dart';
import '../../../../core/usecases/usecase.dart';
import '../entities/paper.dart';
import '../repositories/paper_repository.dart';

class SearchPapers implements UseCase<List<Paper>, String> {
  final PaperRepository repository;

  SearchPapers(this.repository);

  @override
  Future<Either<Failure, List<Paper>>> call(String query) async {
    return await repository.searchPapers(query);
  }
}