import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-extension-tool-details',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './extension-tool-details.component.html',
  styleUrl: './extension-tool-details.component.scss',
})
export class ExtensionToolDetailsComponent {
  @Input() toolId: string | null = null;
}
