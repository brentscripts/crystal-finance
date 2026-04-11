using CrystalFinanceLibrary.Data;
using CrystalFinanceLibrary.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace CrystalFinance.Api.Controllers;

[Route("api/[controller]")]
[ApiController]
[Authorize(Policy = "API.UserAccess")]
public class CrystalFinanceController(IMySqlDataService sqlCrud) : ControllerBase
{
    private readonly IMySqlDataService _data = sqlCrud;

    // GET: api/<CrystalFinanceController>
    [HttpGet]
    public async Task<ActionResult<IEnumerable<TransactionModel>>> Get()
    {
        var output = await _data.GetAllTransactions();
        return output == null || output.Count == 0 ? NotFound("No transactions found.") : Ok(output);
    }

    // GET api/<CrystalFinanceController>/5
    [HttpGet("{id:int:min(1)}")]
    public async Task<ActionResult<TransactionModel?>> Get(int id)
    {
        var output = await _data.GetTransactionById(id);
        return output == null ? NotFound($"Transaction with ID {id} not found.") : Ok(output);
    }

    // POST api/<CrystalFinanceController>
    [HttpPost]
    public async Task<IActionResult> Post([FromBody] TransactionModel value)
    {
        if (value == null)
        {
            return BadRequest("Transaction data is required.");
        }
        
        await _data.AddTransaction(value);

        return Ok(new { message = "Transaction added successfully." });
    }

    // PUT api/<CrystalFinanceController>/5
    [HttpPut("{id:int:min(1)}")]
    public async Task<IActionResult> Put(int id, [FromBody] TransactionModel value)
    {
        if (id != value.Id) return BadRequest("Transaction ID mismatch.");

        await _data.UpdateTransaction(value);

        return Ok(new { message = "Transaction updated successfully." });
    }

    // DELETE api/<CrystalFinanceController>/5
    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(int id)
    {
        var existing = await _data.GetTransactionById(id);
        if (existing == null) return NotFound();

        await _data.DeleteTransaction(id);

        return Ok(new { message = "Transaction deleted successfully." });
    }
}
