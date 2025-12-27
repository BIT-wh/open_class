from float_bubble.main_float_bubble import app
# from gravity_bubble.main_gravity_bubble import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)