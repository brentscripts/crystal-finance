using CrystalFinanceLibrary.Data;
using CrystalFinanceLibrary.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace CrystalFinance.Api.Controllers;

[Route("api/[controller]")]
[ApiController]
[Authorize(Policy = "API.UserAccess")]
public class CrystalFinanceController : ControllerBase
{
    private readonly IMySqlDataService _data;

    public CrystalFinanceController(IMySqlDataService sqlCrud)
    {
        _data = sqlCrud;
    }

    // GET: api/<CrystalFinanceController>
    [HttpGet]
    public async Task<ActionResult<IEnumerable<TransactionModel>>> Get()
    {
        var output = await _data.GetAllTransactions();
        return Ok(output);
    }

    // GET api/<CrystalFinanceController>/5
    [HttpGet("{id}")]
    public string Get(int id)
    {
        return "value";
    }

    // POST api/<CrystalFinanceController>
    [HttpPost]
    public void Post([FromBody] string value)
    {
    }

    // PUT api/<CrystalFinanceController>/5
    [HttpPut("{id}")]
    public void Put(int id, [FromBody] string value)
    {
    }

    // DELETE api/<CrystalFinanceController>/5
    [HttpDelete("{id}")]
    public void Delete(int id)
    {
    }
}
