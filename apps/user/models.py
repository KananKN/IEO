# from apps import db


# class Line(db.Model):
#     __tablename__ = 'Line'
#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     token = db.Column(db.String(100))

#     def __init__(self, token):
#         self.token = token

#     def __repr__(self):
#         return f"<id={self.id},token={self.token},created_at={self.created_at},updated_at={self.updated_at}>"

#     def save(self):
#         # inject self into db session
#         db.session.add(self)
#         # commit change and save the object
#         db.session.commit()
#         return self
