import dearpygui.dearpygui as dpg

dpg.create_context()

with dpg.font_registry():
    with dpg.font("NanumGothic-Bold.ttf", 20) as font1:
        dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
        dpg.add_font_range_hint(dpg.mvFontRangeHint_Korean)

dpg.create_viewport(title='Custom 테스트 Title', width=800, height=600)
dpg.setup_dearpygui()

with dpg.window(label="테스트 윈도우"):
    dpg.add_text("안녕하세요! DearPyGui에서 한국어 테스트 중입니다.", wrap=400, parent=dpg.last_container())
    dpg.add_text("여기는 나눔고딕 폰트로 출력됩니다.", wrap=400)

dpg.bind_font(font1)

dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
