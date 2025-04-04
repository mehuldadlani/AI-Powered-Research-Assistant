// In lib/features/paper_search/domain/entities/paper.dart

import 'package:equatable/equatable.dart';

class Paper extends Equatable {
  final String id;
  final String title;
  final String abstract;
  final List<String> authors;

  const Paper({
    required this.id,
    required this.title,
    required this.abstract,
    required this.authors,
  });

  @override
  List<Object?> get props => [id, title, abstract, authors];
}