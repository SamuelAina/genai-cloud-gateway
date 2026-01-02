using System.Net.Http.Json;

var baseUrl = args.Length > 0 ? args[0] : "http://localhost:8000";

var http = new HttpClient();
http.BaseAddress = new Uri(baseUrl);

var payload = new
{
    prompt = "Rewrite this for a professional email: hey send me the report asap",
    task = "rewrite",
    priority = "low_cost",
    max_output_tokens = 256,
    temperature = 0.2,
    top_p = 0.9
};

Console.WriteLine($"POST {baseUrl}/generate");
var resp = await http.PostAsJsonAsync("/generate", payload);
var body = await resp.Content.ReadAsStringAsync();

Console.WriteLine($"Status: {(int)resp.StatusCode}");
Console.WriteLine(body);
