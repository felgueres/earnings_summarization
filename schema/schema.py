from marshmallow import Schema, fields

class EarningsCallSchema(Schema):
  section = fields.Str()
  role = fields.Str()
  start_idx = fields.Int()
  end_idx = fields.Int()
  text = fields.Str()
  text_tokens = fields.Int()
  summary = fields.Str() 
  summary_tokens = fields.Int()
  cik = fields.Str()
  period = fields.Str()
