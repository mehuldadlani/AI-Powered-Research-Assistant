// In lib/features/paper_search/data/models/paper_model.dart

import 'package:json_annotation/json_annotation.dart';
import '../../domain/entities/paper.dart';

part 'paper_model.g.dart';

@JsonSerializable()
class PaperModel {
  final String id;
  final String title;
  final String abstract;
  final List<String> authors;

  PaperModel({
    required this.id,
    required this.title,
    required this.abstract,
    required this.authors,
  });

  factory PaperModel.fromJson(Map<String, dynamic> json) => _$PaperModelFromJson(json);

  Map<String, dynamic> toJson() => _$PaperModelToJson(this);

  Paper toEntity() {
    return Paper(
      id: id,
      title: title,
      abstract: abstract,
      authors: authors,
    );
  }
}