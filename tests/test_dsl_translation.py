from sansqrit.dsl import translate, run_code


def test_translate_control_flow():
    py = translate('''
let total = 0
for i in range(4) {
  total += i
}
''')
    assert "for i in range(4):" in py


def test_pipeline():
    env = run_code('''
let xs = [1, 2, 3, 4]
let ys = xs |> map(fn(x) => x * x)
let zs = ys |> filter(fn(x) => x > 4)
let total = zs |> sum
''')
    assert env["ys"] == [1, 4, 9, 16]
    assert env["zs"] == [9, 16]
    assert env["total"] == 25
