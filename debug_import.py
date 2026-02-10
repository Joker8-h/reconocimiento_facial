import sys
try:
    import face_recognition_models
    print("face_recognition_models imported successfully")
    print(face_recognition_models.__file__)
except Exception as e:
    print(f"Error importing face_recognition_models: {e}")
    import traceback
    traceback.print_exc()
