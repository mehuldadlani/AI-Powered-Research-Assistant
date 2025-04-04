import 'package:dartz/dartz.dart';
import '../../../../core/error/failures.dart';
import '../entities/paper.dart';

abstract class PaperRepository {
  Future<Either<Failure, List<Paper>>> getPapers();
  Future<Either<Failure, List<Paper>>> searchPapers(String query);
}