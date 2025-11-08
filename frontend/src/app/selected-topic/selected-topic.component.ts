import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { DefaultService } from '../client';
import { ApiError } from '../client/core/ApiError';

@Component({
  selector: 'app-selected-topic',
  imports: [CommonModule, FormsModule, MatFormFieldModule, MatInputModule, MatButtonModule],
  templateUrl: './selected-topic.component.html',
  styleUrl: './selected-topic.component.scss'
})

export class SelectedTopicComponent {
  query: string = '';
  result: string | null = null;

  protected async ctaClick() {
    var res = await DefaultService.runProofOfConceptPocGet();
    console.log('cta called', res);
  }

  async checkPocGet(): Promise<void> {
    this.result = 'Loading...';
    try {
      const res = await DefaultService.checkChromadbCheckGet(this.query);
      // show the entered query plus the API response for clarity
      this.result = `Query: ${this.query} \nResponse: ${JSON.stringify(res)}`;
    } catch (err: any) {
      // If the generated client threw an ApiError with status 500, show a clearer message
      if (err instanceof ApiError && err.status === 500) {
        this.result = `Server error (500): ${err.message}`;
      } else {
        this.result = `Error: ${err?.message ?? JSON.stringify(err)}`;
      }
    }
  }

}
