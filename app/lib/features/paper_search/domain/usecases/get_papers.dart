import 'package:dartz/dartz.dart';
import '../../../../core/error/failures.dart';
import '../../../../core/usecases/usecase.dart';
import '../entities/paper.dart';
import '../repositories/paper_repository.dart';

class GetPapers implements UseCase<List<Paper>, NoParams> {
  final PaperRepository repository;

  GetPapers(this.repository);

  @override
  Future<Either<Failure, List<Paper>>> call(NoParams params) async {
    return await repository.getPapers();
  }
}